from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


SIDE_EFFECTS = (
    "read_only",
    "writes_report",
    "writes_manifest",
    "writes_save_state",
    "writes_generated_artifact",
    "executes_emulator",
    "rebuilds_rom",
    "patches_source",
    "network",
    "destructive",
)

READ_ONLY_FORBIDDEN_EFFECTS = {
    "writes_report",
    "writes_manifest",
    "writes_save_state",
    "writes_generated_artifact",
    "rebuilds_rom",
    "patches_source",
    "network",
    "destructive",
}

# Output-destination flags. A command whose declared side effects are clean is
# still refused under --read-only when the invocation explicitly requests a
# file write through one of these. Matched on raw argv including argparse
# abbreviations and "--flag=path" forms so the check guards v2 verbs
# that own their argparse; a positional value that happens to equal a flag
# string is refused too, which errs in the safe direction.
READ_ONLY_OUTPUT_FLAGS = (
    "--json-out",
    "--out",
    "--markdown-out",
    "--manifest-out",
    "--save-state-out",
    "--log-out",
    "--search-log-out",
)


@dataclass(frozen=True)
class CommandMetadata:
    command_id: str
    command: str
    owner: str
    side_effects: tuple[str, ...]
    notes: str = ""

    @property
    def read_only_safe(self) -> bool:
        return not (set(self.side_effects) & READ_ONLY_FORBIDDEN_EFFECTS)

    def to_jsonable(self) -> dict[str, object]:
        return {
            "command_id": self.command_id,
            "command": self.command,
            "owner": self.owner,
            "side_effects": list(self.side_effects),
            "read_only_safe": self.read_only_safe,
            "notes": self.notes,
        }


TRACE_COMMANDS = (
    "boss_ai_trace_capture",
    "boss_ai_trace_batch",
    "boss_ai_trace_state_probe",
    "boss_ai_state_replay",
    "boss_ai_state_factory",
    "boss_ai_shared_switch_loop_fixture",
)


def all_command_metadata() -> list[CommandMetadata]:
    rows: list[CommandMetadata] = []
    rows.extend(debugger_command_metadata())
    rows.extend(boss_ai_command_metadata())
    rows.extend(trace_command_metadata())
    return sorted(rows, key=lambda item: item.command_id)


def metadata_by_id() -> dict[str, CommandMetadata]:
    return {item.command_id: item for item in all_command_metadata()}


def taxonomy_summary() -> dict[str, object]:
    rows = all_command_metadata()
    unknown = [item for item in rows if not item.side_effects]
    effect_counts = {name: 0 for name in SIDE_EFFECTS}
    for item in rows:
        for effect in item.side_effects:
            effect_counts[effect] = effect_counts.get(effect, 0) + 1
    return {
        "schema_version": 1,
        "kind": "debugger_command_side_effect_taxonomy",
        "command_count": len(rows),
        "read_only_refusal_enforced": True,
        "side_effect_unknown_command_count": len(unknown),
        "read_only_safe_count": sum(1 for item in rows if item.read_only_safe),
        "read_only_refused_count": sum(1 for item in rows if not item.read_only_safe),
        "effect_counts": effect_counts,
        "unknown_commands": [item.command_id for item in unknown],
        "commands": [item.to_jsonable() for item in rows],
    }


def read_only_refusal_for(command_id: str, argv: Iterable[str] = ()) -> str | None:
    metadata = metadata_by_id().get(command_id)
    if metadata is None:
        return f"read-only mode refuses {command_id}: command metadata is missing"
    forbidden = sorted(set(metadata.side_effects) & READ_ONLY_FORBIDDEN_EFFECTS)
    if forbidden:
        return (
            f"read-only mode refuses {command_id}: "
            f"declared side effects include {', '.join(forbidden)}"
        )
    exact_options: set[str] = set()
    if command_id.startswith(("debugger:", "debugger-v2:", "boss-ai:")):
        if command_id.startswith("boss-ai:"):
            from tools.boss_ai_debugger.parsers import build_parser
        else:
            from .parsers import build_parser
        from .parsers import command_parsers
        command = command_parsers(build_parser()).get(command_id.split(":", 1)[1])
        if command is not None:
            exact_options = {option for action in command._actions for option in action.option_strings}
    options = {arg.split("=", 1)[0] for arg in argv if arg.startswith("--") and arg != "--"}
    requested_outputs = sorted(
        {
            flag
            for option in options
            for flag in READ_ONLY_OUTPUT_FLAGS
            if option == flag or (option not in exact_options and flag.startswith(option))
        }
    )
    if requested_outputs:
        return (
            f"read-only mode refuses {command_id}: "
            f"output flags request file writes ({', '.join(requested_outputs)})"
        )
    return None


def debugger_command_metadata() -> list[CommandMetadata]:
    from .parsers import build_parser, command_parsers

    rows = []
    for name, parser in command_parsers(build_parser()).items():
        module = parser.get_default("command_module")
        rows.append(CommandMetadata(
            command_id=parser.get_default("command_id"),
            command=f"python -m tools.debugger {name}",
            owner="unified_debugger_v2" if module else "unified_debugger",
            side_effects=parser.get_default("side_effects"),
            notes=f"passthrough module {module}" if module else "shared parser command",
        ))
    return rows


def boss_ai_command_metadata() -> list[CommandMetadata]:
    return [
        CommandMetadata(
            command_id=f"boss-ai:{name}",
            command=f"python -m tools.boss_ai_debugger {name}",
            owner="boss_ai_debugger",
            side_effects=_effects_for_boss_ai_command(name),
            notes="Boss AI debugger parser command",
        )
        for name in _boss_ai_command_names()
    ]


def trace_command_metadata() -> list[CommandMetadata]:
    return [
        CommandMetadata(
            command_id=f"trace:{name}",
            command=f"python tools\\trace\\{name}.py",
            owner="trace_runtime",
            side_effects=_effects_for_trace_command(name),
            notes="standalone trace runtime script",
        )
        for name in TRACE_COMMANDS
    ]


def _boss_ai_command_names() -> tuple[str, ...]:
    from tools.boss_ai_debugger.parsers import build_parser

    return _subparser_names(build_parser())


def _subparser_names(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return tuple(sorted(action.choices))
    return ()


def _effects_for_boss_ai_command(name: str) -> tuple[str, ...]:
    effects = ["read_only"]
    writes_report = {
        "report",
        "regress",
        "batch-simulate",
        "trace-replay",
        "state-schema",
        "rule-map",
        "generate",
        "replay-import",
        "coverage-search",
        "review-queue",
        "run-suite",
        "metamorphic",
        "mutate",
        "mastery-index",
        "coverage-report",
        "confidence-report",
        "counterfactual",
        "minimize",
        "localize",
        "route-eval",
        "diff",
        "decision-trace",
        "explain-decision",
        "python-contribution-trace",
        "rom-contribution-trace",
        "rom-selector-materialize",
        "rom-score-materialize",
        "rom-switch-materialize",
        "rom-counterfactual-materialize",
        "haki-coverage",
        "role-packages",
        "coach-plan-templates",
        "move-score-probe",
        "damage-ai-report",
    }
    generated = {
        "report",
        "generate",
        "replay-import",
        "coverage-search",
        "review-queue",
        "run-suite",
        "mastery-index",
        "coverage-report",
        "confidence-report",
        "counterfactual",
        "minimize",
        "localize",
        "diff",
        "decision-trace",
        "explain-decision",
        "python-contribution-trace",
        "rom-contribution-trace",
        "rom-selector-materialize",
        "rom-score-materialize",
        "rom-switch-materialize",
        "rom-counterfactual-materialize",
    }
    emulator = {
        "run-suite",
        "move-score-probe",
        "damage-ai-report",
        "rom-contribution-trace",
        "rom-selector-materialize",
        "rom-score-materialize",
        "rom-switch-materialize",
        "rom-counterfactual-materialize",
    }
    if name == "judge":
        effects.append("writes_manifest")
    if name in writes_report:
        effects.append("writes_report")
    if name in generated:
        effects.append("writes_generated_artifact")
    if name in emulator:
        effects.append("executes_emulator")
    if name == "run-suite":
        effects.extend(("rebuilds_rom", "writes_manifest"))
    return _dedupe(effects)


def _effects_for_trace_command(name: str) -> tuple[str, ...]:
    effects = ["read_only", "executes_emulator", "writes_report"]
    if name in {"boss_ai_state_factory", "boss_ai_shared_switch_loop_fixture"}:
        effects.extend(("writes_save_state", "writes_manifest", "writes_generated_artifact"))
    if name == "boss_ai_trace_batch":
        effects.extend(("writes_manifest", "writes_generated_artifact"))
    return _dedupe(effects)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        if value not in SIDE_EFFECTS:
            raise ValueError(f"unknown side effect: {value}")
        if value not in out:
            out.append(value)
    if set(out) & READ_ONLY_FORBIDDEN_EFFECTS:
        out = [value for value in out if value != "read_only"]
    return tuple(out)
