from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .catalog import ROOT


SCHEMA_VERSION = 1
DEFAULT_BACKEND_ORDER = ("pyboy", "sameboy", "gambatte", "vba-m")
DEFAULT_CONFORMANCE_STORE = Path("audit") / "crossemu_conformance.jsonl"

ModuleFinder = Callable[[str], Any]
CommandFinder = Callable[[str], str | None]


@dataclass(frozen=True)
class BackendSpec:
    name: str
    display_name: str
    role: str
    python_modules: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    install_steps: tuple[str, ...] = ()
    notes: str = ""


BACKENDS: dict[str, BackendSpec] = {
    "pyboy": BackendSpec(
        name="pyboy",
        display_name="PyBoy",
        role="canonical",
        python_modules=("pyboy",),
        commands=("pyboy",),
        install_steps=("python -m pip install pyboy",),
        notes="Canonical local automation backend; still not proof for VBA/VBA-M-only symptoms.",
    ),
    "sameboy": BackendSpec(
        name="sameboy",
        display_name="SameBoy",
        role="cross_backend",
        commands=("sameboy", "sameboy-headless", "SameBoy.exe"),
        install_steps=(
            "Install a SameBoy CLI/headless build and put the executable on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends sameboy",
        ),
        notes="Preferred timing-sensitive cross-check once a headless binary is available.",
    ),
    "gambatte": BackendSpec(
        name="gambatte",
        display_name="gambatte",
        role="cross_backend",
        commands=("gambatte-speedrun", "gambatte", "gambatte_sdl"),
        install_steps=(
            "Install gambatte-speedrun or another scriptable gambatte build on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends gambatte",
        ),
        notes="Useful as a second CPU/PPU implementation once conformance-gated.",
    ),
    "vba-m": BackendSpec(
        name="vba-m",
        display_name="VisualBoyAdvance-M (VBA-M)",
        role="cross_backend",
        commands=("visualboyadvance-m", "vbam", "vba-m", "VisualBoyAdvance-M.exe"),
        install_steps=(
            "Install VisualBoyAdvance-M with a CLI/headless entry point on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends vba-m",
        ),
        notes="Targets the May 2026 user-reported VBA/VBA-M divergence class.",
    ),
}

BACKEND_ALIASES = {
    "vbam": "vba-m",
    "vba": "vba-m",
    "visualboyadvance-m": "vba-m",
    "visual-boy-advance-m": "vba-m",
}


def normalize_backend_name(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    return BACKEND_ALIASES.get(key, key)


def parse_backend_list(spec: str | Sequence[str] | None) -> tuple[str, ...]:
    if spec is None:
        return DEFAULT_BACKEND_ORDER
    parts: list[str] = []
    if isinstance(spec, str):
        raw_items = spec.replace(";", ",").split(",")
    else:
        raw_items = []
        for item in spec:
            raw_items.extend(str(item).replace(";", ",").split(","))
    for raw in raw_items:
        name = normalize_backend_name(raw)
        if name and name not in parts:
            parts.append(name)
    return tuple(parts or DEFAULT_BACKEND_ORDER)


def build_preflight_report(
    *,
    backends: str | Sequence[str] | None = None,
    conformance_store: str | Path = DEFAULT_CONFORMANCE_STORE,
    conformance_rows: Iterable[Mapping[str, Any]] | None = None,
    root: Path = ROOT,
    module_finder: ModuleFinder = importlib.util.find_spec,
    command_finder: CommandFinder = shutil.which,
) -> dict[str, Any]:
    requested = parse_backend_list(backends)
    errors = [f"unknown backend {name!r}" for name in requested if name not in BACKENDS]
    rows, row_errors = _conformance_rows(
        conformance_store=conformance_store,
        conformance_rows=conformance_rows,
        root=root,
    )
    errors.extend(row_errors)

    entries = [
        _discover_backend(
            BACKENDS[name],
            conformance_rows=rows,
            module_finder=module_finder,
            command_finder=command_finder,
        )
        for name in requested
        if name in BACKENDS
    ]
    by_name = {entry["name"]: entry for entry in entries}
    pyboy = by_name.get("pyboy")
    cross_backends = [entry for entry in entries if entry["role"] == "cross_backend"]
    available_cross = [entry for entry in cross_backends if entry["available"]]
    trusted_cross = [entry for entry in cross_backends if entry["trusted_for_differential"]]

    blocking_reasons: list[str] = []
    if pyboy is None:
        blocking_reasons.append("pyboy backend was not selected")
    elif not pyboy["available"]:
        blocking_reasons.append("pyboy backend is not available for canonical run")
    if not available_cross:
        blocking_reasons.append("no cross-emulator backend is installed")
    elif not trusted_cross:
        blocking_reasons.append("no conformance-passing cross-emulator backend is installed")

    return {
        "kind": "unified_debugger_crossemu_preflight",
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "requested_backends": list(requested),
        "available_count": sum(1 for entry in entries if entry["available"]),
        "cross_backend_available_count": len(available_cross),
        "trusted_cross_backend_count": len(trusted_cross),
        "ready_for_pyboy_run": bool(pyboy and pyboy["available"]),
        "ready_for_cross_backend_diff": bool(pyboy and pyboy["available"] and trusted_cross),
        "blocking_reasons": blocking_reasons,
        "backends": entries,
        "errors": errors,
        "conformance_store": str(_resolve_path(conformance_store, root=root)),
    }


def build_install_docs_report(
    *,
    backends: str | Sequence[str] | None = None,
    missing_only: bool = True,
    root: Path = ROOT,
    module_finder: ModuleFinder = importlib.util.find_spec,
    command_finder: CommandFinder = shutil.which,
) -> dict[str, Any]:
    preflight = build_preflight_report(
        backends=backends,
        conformance_rows=(),
        root=root,
        module_finder=module_finder,
        command_finder=command_finder,
    )
    recipes: list[dict[str, Any]] = []
    for entry in preflight["backends"]:
        if missing_only and entry["available"]:
            continue
        spec = BACKENDS[entry["name"]]
        recipes.append(
            {
                "name": spec.name,
                "display_name": spec.display_name,
                "available": entry["available"],
                "install_steps": list(spec.install_steps),
                "verify_command": (
                    f"python -m tools.debugger crossemu preflight --backends {spec.name}"
                ),
                "notes": spec.notes,
            }
        )
    return {
        "kind": "unified_debugger_crossemu_install_docs",
        "schema_version": SCHEMA_VERSION,
        "valid": preflight["valid"],
        "missing_only": missing_only,
        "recipes": recipes,
        "errors": list(preflight["errors"]),
    }


def run_self_test() -> dict[str, Any]:
    def fake_module_finder(name: str) -> object | None:
        return object() if name == "pyboy" else None

    def fake_command_finder(name: str) -> str | None:
        return "C:/tools/sameboy.exe" if name == "sameboy-headless" else None

    report = build_preflight_report(
        backends=("pyboy", "sameboy", "gambatte"),
        conformance_rows=(
            {"backend": "sameboy", "status": "pass", "suite": "selftest"},
            {"backend": "gambatte", "status": "fail", "suite": "selftest"},
        ),
        module_finder=fake_module_finder,
        command_finder=fake_command_finder,
    )
    return {
        "kind": "unified_debugger_crossemu_selftest",
        "schema_version": SCHEMA_VERSION,
        "passed": bool(report["valid"] and report["ready_for_cross_backend_diff"]),
        "preflight": report,
    }


def _discover_backend(
    spec: BackendSpec,
    *,
    conformance_rows: Sequence[Mapping[str, Any]],
    module_finder: ModuleFinder,
    command_finder: CommandFinder,
) -> dict[str, Any]:
    probes: list[dict[str, Any]] = []
    availability_proof = ""
    for module in spec.python_modules:
        found = module_finder(module)
        probe = {
            "kind": "python_module",
            "name": module,
            "available": found is not None,
            "path": _module_origin(found),
        }
        probes.append(probe)
        if found is not None and not availability_proof:
            availability_proof = f"python_module:{module}"
    for command in spec.commands:
        found_path = command_finder(command)
        probe = {
            "kind": "command",
            "name": command,
            "available": bool(found_path),
            "path": str(found_path or ""),
        }
        probes.append(probe)
        if found_path and not availability_proof:
            availability_proof = f"command:{command}"

    conformance_status = _latest_conformance_status(spec.name, conformance_rows)
    available = bool(availability_proof)
    return {
        "name": spec.name,
        "display_name": spec.display_name,
        "role": spec.role,
        "status": "available" if available else "missing",
        "available": available,
        "availability_proof": availability_proof,
        "missing_reason": "" if available else "no Python module or executable found",
        "discovery": probes,
        "conformance_status": conformance_status,
        "trusted_for_differential": available and conformance_status == "pass",
        "install_hint": spec.install_steps[0] if spec.install_steps else "",
        "notes": spec.notes,
    }


def _latest_conformance_status(backend: str, rows: Sequence[Mapping[str, Any]]) -> str:
    latest = "missing"
    for row in rows:
        if normalize_backend_name(str(row.get("backend", ""))) != backend:
            continue
        status = str(
            row.get("status")
            or row.get("result")
            or row.get("outcome")
            or ""
        ).strip().lower()
        if status in {"pass", "passed", "ok"}:
            latest = "pass"
        elif status in {"fail", "failed", "error"}:
            latest = "fail"
        else:
            latest = "unknown"
    return latest


def _conformance_rows(
    *,
    conformance_store: str | Path,
    conformance_rows: Iterable[Mapping[str, Any]] | None,
    root: Path,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    if conformance_rows is not None:
        return list(conformance_rows), []
    path = _resolve_path(conformance_store, root=root)
    if not path.exists():
        return [], []
    rows: list[Mapping[str, Any]] = []
    errors: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{lineno}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(decoded, dict):
            errors.append(f"{path}:{lineno}: expected object row")
            continue
        rows.append(decoded)
    return rows, errors


def _resolve_path(path: str | Path, *, root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _module_origin(candidate: Any) -> str:
    origin = getattr(candidate, "origin", "")
    return str(origin or "")


def format_preflight(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu preflight: {status}"]
    for entry in report.get("backends", []):
        proof = entry.get("availability_proof") or entry.get("missing_reason") or "unknown"
        lines.append(f"  {entry['name']}: {entry['status']} ({proof})")
        lines.append(f"    conformance: {entry.get('conformance_status', 'missing')}")
    lines.append(f"ready_for_pyboy_run: {_yes_no(report.get('ready_for_pyboy_run'))}")
    lines.append(
        f"ready_for_cross_backend_diff: {_yes_no(report.get('ready_for_cross_backend_diff'))}"
    )
    blocking = report.get("blocking_reasons") or ()
    if blocking:
        lines.append("blocking_reasons:")
        lines.extend(f"  - {reason}" for reason in blocking)
    errors = report.get("errors") or ()
    if errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in errors)
    return "\n".join(lines)


def format_install_docs(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu install-docs: {status}"]
    recipes = report.get("recipes") or ()
    if not recipes:
        lines.append("all requested backends are currently discoverable")
    for recipe in recipes:
        lines.append(f"{recipe['name']} ({recipe['display_name']}):")
        for step in recipe.get("install_steps", []):
            lines.append(f"  - {step}")
        lines.append(f"  verify: {recipe['verify_command']}")
    errors = report.get("errors") or ()
    if errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in errors)
    return "\n".join(lines)


def _yes_no(value: Any) -> str:
    return "yes" if value else "no"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger crossemu",
        description="Cross-emulator differential preflight and install guidance.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser(
        "preflight",
        help="Discover emulator backends and report whether cross-emulator diffing is gated.",
    )
    preflight.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKEND_ORDER),
        help="Comma-separated backend list, default: pyboy,sameboy,gambatte,vba-m.",
    )
    preflight.add_argument(
        "--conformance-store",
        default=str(DEFAULT_CONFORMANCE_STORE),
        help="JSONL conformance result store used to mark cross backends trusted.",
    )
    preflight.add_argument("--json", action="store_true")
    preflight.set_defaults(func=cmd_preflight)

    install_docs = sub.add_parser(
        "install-docs",
        help="Print install/verify recipes for missing cross-emulator backends.",
    )
    install_docs.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKEND_ORDER),
        help="Comma-separated backend list, default: pyboy,sameboy,gambatte,vba-m.",
    )
    install_docs.add_argument(
        "--all",
        action="store_true",
        help="Show recipes for all requested backends, not just missing ones.",
    )
    install_docs.add_argument("--json", action="store_true")
    install_docs.set_defaults(func=cmd_install_docs)
    return parser


def cmd_preflight(args: argparse.Namespace) -> int:
    report = build_preflight_report(
        backends=args.backends,
        conformance_store=args.conformance_store,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_preflight(report))
    return 0 if report["valid"] else 1


def cmd_install_docs(args: argparse.Namespace) -> int:
    report = build_install_docs_report(
        backends=args.backends,
        missing_only=not args.all,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_install_docs(report))
    return 0 if report["valid"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
