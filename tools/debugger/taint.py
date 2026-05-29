from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT
from .ingest import sha256_file
from .provenance import (
    collect_source_paths,
    derive_report_provenance_inputs,
    display_path,
    parse_symbol_table,
    resolve_path,
)
from .reporting import load_reports
from .slicing import (
    IGNORED_TOKENS,
    TOKEN_RE,
    canonical_label,
    match_label_definition,
    strip_comment,
)
from .workflow import command_is_runnable


REGISTER_NAMES = {
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "h",
    "l",
    "af",
    "bc",
    "de",
    "hl",
    "sp",
}
REGISTER_PARTS = {
    "af": ("a", "f"),
    "bc": ("b", "c"),
    "de": ("d", "e"),
    "hl": ("h", "l"),
}
POINTER_ALIASES = {
    "[bc]": "bc",
    "[de]": "de",
    "[hl]": "hl",
    "[hli]": "hl",
    "[hld]": "hl",
    "[hl+]": "hl",
    "[hl-]": "hl",
}
VALUE_OPS = {"add", "adc", "sub", "sbc", "and", "or", "xor"}
MUTATING_OPS = {"inc", "dec", "set", "res", "sla", "sra", "srl", "swap", "rl", "rr", "rlc", "rrc"}


def build_taint_report(
    *,
    symbols_path: str = "pokegold.sym",
    reports: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    source_files: tuple[str, ...] = (),
    max_depth: int = 80,
    max_paths: int = 40,
    root: Path = ROOT,
) -> dict[str, Any]:
    sym_path = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []

    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    errors.extend(report_errors)
    derived_inputs = derive_report_provenance_inputs(loaded_reports)
    effective_symbols = tuple(unique_list([*symbols, *derived_inputs["symbols"]]))
    effective_source_files = tuple(unique_list([*source_files, *derived_inputs["source_files"]]))

    if not effective_symbols:
        errors.append("at least one --symbol or report-derived symbol is required")
    if max_depth < 1:
        errors.append("--max-depth must be positive")
    if max_paths < 1:
        errors.append("--max-paths must be positive")

    symbol_table: dict[str, dict[str, Any]] = {}
    if sym_path.exists():
        symbol_table = parse_symbol_table(sym_path)
    else:
        errors.append(f"missing symbol file: {symbols_path}")

    source_paths, source_errors = select_source_paths(source_files=effective_source_files, root=root)
    errors.extend(source_errors)
    routines = parse_source_routines(source_paths=source_paths, symbol_table=symbol_table, root=root)
    known_symbols = set(symbol_table) | set(routines)

    targets = [
        analyze_target(
            symbol,
            routines=routines,
            known_symbols=known_symbols,
            max_depth=max(1, max_depth),
            max_paths=max(1, max_paths),
        )
        for symbol in effective_symbols
    ]
    warnings.extend(
        warning
        for target in targets
        for warning in target.get("warnings", [])
    )
    paths = [
        path
        for target in targets
        for path in target.get("paths", [])
    ][:max_paths]
    commands = unique_list(
        command
        for target in targets
        for command in target.get("commands", [])
    )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_taint_report",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "input_reports": [item["source"] for item in loaded_reports],
        "input_symbols": list(symbols),
        "input_source_files": list(source_files),
        "derived_report_symbols": derived_inputs["symbols"],
        "derived_report_source_files": derived_inputs["source_files"],
        "symbols_path": display_path(sym_path, root=root),
        "symbols_sha256": sha256_file(sym_path) if sym_path.exists() else "",
        "symbols": list(effective_symbols),
        "source_files": list(effective_source_files),
        "source_file_count": len(source_paths),
        "routine_count": len(routines),
        "target_count": len(targets),
        "sink_count": sum(int(target.get("sink_count", 0)) for target in targets),
        "contributor_count": sum(int(target.get("contributor_count", 0)) for target in targets),
        "path_count": len(paths),
        "targets": targets,
        "paths": paths,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This is bounded source-level SM83-style backward dataflow over RGBDS assembly, not emulator-backed dynamic taint.",
            "Indirect pointer writes are linked only when the source assigns the pointer in the same routine window.",
            "Calls are reported as transform boundaries unless a focused subsystem trace proves their internal effects.",
        ],
    }


def select_source_paths(*, source_files: tuple[str, ...], root: Path) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    if source_files:
        paths: list[Path] = []
        for raw_path in source_files:
            path = resolve_path(raw_path, root=root)
            if not path.exists():
                errors.append(f"source path does not exist: {raw_path}")
                continue
            if path.is_dir():
                errors.append(f"source path is a directory: {raw_path}")
                continue
            if path.suffix.lower() != ".asm":
                errors.append(f"source path is not an asm file: {raw_path}")
                continue
            paths.append(path)
        return sorted(paths, key=lambda item: display_path(item, root=root)), errors
    return [
        path
        for path in collect_source_paths(root=root, include_docs=False, explicit_paths=())
        if path.suffix.lower() == ".asm"
    ], errors


def parse_source_routines(
    *,
    source_paths: list[Path],
    symbol_table: dict[str, dict[str, Any]],
    root: Path,
) -> dict[str, dict[str, Any]]:
    routines: dict[str, dict[str, Any]] = {}
    for path in source_paths:
        display = display_path(path, root=root)
        current_label = ""
        current_global = ""
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, text in enumerate(lines, 1):
            raw_label = match_label_definition(text)
            code = strip_comment(text)
            if raw_label:
                label = canonical_label(raw_label, current_global=current_global)
                if not raw_label.startswith("."):
                    current_global = raw_label
                current_label = label
                routines.setdefault(
                    label,
                    {
                        "label": label,
                        "path": display,
                        "line": line_no,
                        "address": symbol_table.get(label),
                        "instructions": [],
                    },
                )
                code = remove_leading_label(code, raw_label)
            if not current_label:
                continue
            instruction = parse_instruction(
                code,
                routine=current_label,
                parent=current_global,
                path=display,
                line=line_no,
            )
            if instruction is None:
                continue
            instruction["index"] = len(routines[current_label]["instructions"])
            routines[current_label]["instructions"].append(instruction)
    return routines


def parse_instruction(
    code: str,
    *,
    routine: str,
    parent: str,
    path: str,
    line: int,
) -> dict[str, Any] | None:
    stripped = code.strip()
    if not stripped:
        return None
    if stripped.startswith((".", "@")) and " " not in stripped and "\t" not in stripped:
        return None
    parts = stripped.split(None, 1)
    op = parts[0].lower()
    operands = split_operands(parts[1] if len(parts) > 1 else "")
    return {
        "routine": routine,
        "parent": parent,
        "path": path,
        "line": line,
        "code": stripped[:220],
        "op": op,
        "operands": operands,
    }


def analyze_target(
    symbol: str,
    *,
    routines: dict[str, dict[str, Any]],
    known_symbols: set[str],
    max_depth: int,
    max_paths: int,
) -> dict[str, Any]:
    sinks = find_sinks(symbol, routines=routines, known_symbols=known_symbols)
    paths = [
        backward_path(
            target=symbol,
            sink=sink,
            routines=routines,
            known_symbols=known_symbols,
            max_depth=max_depth,
        )
        for sink in sinks[:max_paths]
    ]
    contributors = merge_contributors(
        contributor
        for path in paths
        for contributor in path.get("contributors", [])
    )
    warnings = []
    if not sinks:
        warnings.append(f"no source-level writes found for taint target: {symbol}")
    commands = commands_for_target(symbol=symbol, contributors=contributors)
    return {
        "symbol": symbol,
        "found": bool(sinks),
        "sink_count": len(sinks),
        "contributor_count": len(contributors),
        "sinks": [sink_summary(sink) for sink in sinks[:max_paths]],
        "contributors": contributors,
        "paths": paths,
        "commands": commands,
        "warnings": warnings,
    }


def find_sinks(
    target: str,
    *,
    routines: dict[str, dict[str, Any]],
    known_symbols: set[str],
) -> list[dict[str, Any]]:
    sinks: list[dict[str, Any]] = []
    for routine in routines.values():
        instructions = routine["instructions"]
        for index, instruction in enumerate(instructions):
            access = write_access(instruction, target, instructions[:index], known_symbols=known_symbols)
            if not access:
                continue
            sink = {
                "target": target,
                "routine": routine["label"],
                "path": instruction["path"],
                "line": instruction["line"],
                "index": index,
                "op": instruction["op"],
                "operands": instruction["operands"],
                "code": instruction["code"],
                "access": access["access"],
                "source_operands": access["source_operands"],
                "pointer_register": access.get("pointer_register", ""),
                "pointer_source": access.get("pointer_source", ""),
            }
            sinks.append(sink)
    return sorted(sinks, key=lambda item: (item["path"], int(item["line"]), item["routine"]))


def write_access(
    instruction: dict[str, Any],
    target: str,
    previous: list[dict[str, Any]],
    *,
    known_symbols: set[str],
) -> dict[str, Any] | None:
    op = instruction["op"]
    operands = instruction["operands"]
    if not operands:
        return None
    if op in {"ld", "ldh"} and len(operands) >= 2:
        destination = operands[0]
        source = operands[1]
        if operand_mentions_symbol(destination, target, current_global=instruction["parent"], known_symbols=known_symbols):
            return {"access": "direct_write", "source_operands": [source]}
        pointer = pointer_alias(destination)
        if pointer:
            pointer_source = last_pointer_assignment(pointer, previous, current_global=instruction["parent"], known_symbols=known_symbols)
            if pointer_source == target:
                return {
                    "access": "indirect_write",
                    "source_operands": [source],
                    "pointer_register": pointer,
                    "pointer_source": pointer_source,
                }
    if op in MUTATING_OPS:
        destination = operands[-1]
        if operand_mentions_symbol(destination, target, current_global=instruction["parent"], known_symbols=known_symbols):
            return {"access": "direct_mutation", "source_operands": [destination]}
        pointer = pointer_alias(destination)
        if pointer:
            pointer_source = last_pointer_assignment(pointer, previous, current_global=instruction["parent"], known_symbols=known_symbols)
            if pointer_source == target:
                return {
                    "access": "indirect_mutation",
                    "source_operands": [destination],
                    "pointer_register": pointer,
                    "pointer_source": pointer_source,
                }
    return None


def backward_path(
    *,
    target: str,
    sink: dict[str, Any],
    routines: dict[str, dict[str, Any]],
    known_symbols: set[str],
    max_depth: int,
) -> dict[str, Any]:
    routine = routines.get(sink["routine"], {})
    instructions = routine.get("instructions", [])
    tainted_registers = registers_from_operands(sink["source_operands"])
    pointer_registers: set[str] = set()
    contributors: list[dict[str, Any]] = []
    steps = [step_from_sink(sink)]

    if sink["access"].endswith("mutation"):
        contributors.append(
            contributor(
                symbol=target,
                relation="previous_state",
                instruction=sink,
                register="",
                evidence="mutation depends on the prior value of the target state",
                confidence=0.72,
            )
        )
    if sink.get("pointer_source"):
        contributors.append(
            contributor(
                symbol=sink["pointer_source"],
                relation="pointer_target",
                instruction=sink,
                register=sink.get("pointer_register", ""),
                evidence=f"{sink.get('pointer_register')} points at the target write address",
                confidence=0.74,
            )
        )

    start = max(0, int(sink["index"]) - max_depth)
    for instruction in reversed(instructions[start:int(sink["index"])]):
        before_count = len(contributors)
        tainted_registers, pointer_registers, new_contributors = transfer_backward(
            instruction,
            tainted_registers=tainted_registers,
            pointer_registers=pointer_registers,
            known_symbols=known_symbols,
        )
        contributors.extend(new_contributors)
        if new_contributors or len(contributors) != before_count:
            steps.append(step_from_instruction(instruction, new_contributors))
        if not tainted_registers and not pointer_registers:
            break

    contributors = merge_contributors(contributors)
    steps = list(reversed(steps))
    confidence = confidence_for_path(sink, contributors)
    return {
        "id": safe_id(f"taint:{target}:{sink['path']}:{sink['line']}"),
        "title": f"{target} {sink['access']} in {sink['routine']}",
        "target": target,
        "routine": sink["routine"],
        "source_file": sink["path"],
        "line": sink["line"],
        "access": sink["access"],
        "confidence": confidence,
        "score": min(96, int(60 + 12 * len(contributors) + confidence * 10)),
        "contributors": contributors,
        "steps": steps,
        "evidence": [
            f"{sink['access']} at {sink['path']}:{sink['line']}",
            *[item["evidence"] for item in contributors[:4]],
        ],
        "related_symbols": unique_list([target, *[item["symbol"] for item in contributors]]),
        "related_files": unique_list([sink["path"], *[item.get("source_file", "") for item in contributors]]),
        "commands": commands_for_target(symbol=target, contributors=contributors),
    }


def transfer_backward(
    instruction: dict[str, Any],
    *,
    tainted_registers: set[str],
    pointer_registers: set[str],
    known_symbols: set[str],
) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    registers = set(tainted_registers)
    pointers = set(pointer_registers)
    contributors: list[dict[str, Any]] = []
    op = instruction["op"]
    operands = instruction["operands"]

    if op in {"ld", "ldh"} and len(operands) >= 2:
        destination = operands[0]
        source = operands[1]
        destination_registers = registers_from_operand(destination)
        destination_pointer = register_name(destination)
        if destination_pointer in pointers:
            pointers.remove(destination_pointer)
            symbols = operand_symbols(source, current_global=instruction["parent"], known_symbols=known_symbols)
            contributors.extend(
                contributor(
                    symbol=symbol,
                    relation="pointer_target",
                    instruction=instruction,
                    register=destination_pointer,
                    evidence=f"{destination_pointer} loaded with address {symbol}",
                    confidence=0.74,
                )
                for symbol in symbols
            )
            registers.update(registers_from_operand(source))
        if destination_registers & registers:
            registers.difference_update(destination_registers)
            source_pointer = pointer_alias(source)
            if source_pointer:
                pointers.add(source_pointer)
            symbols = operand_symbols(source, current_global=instruction["parent"], known_symbols=known_symbols)
            relation = "memory_load" if is_memory_operand(source) else "immediate_or_address"
            confidence = 0.82 if is_memory_operand(source) else 0.58
            contributors.extend(
                contributor(
                    symbol=symbol,
                    relation=relation,
                    instruction=instruction,
                    register=", ".join(sorted(destination_registers)),
                    evidence=f"{instruction['code']} feeds {', '.join(sorted(destination_registers))}",
                    confidence=confidence,
                )
                for symbol in symbols
            )
            registers.update(registers_from_operand(source))

    elif op in VALUE_OPS and "a" in registers:
        for operand in operands:
            if register_name(operand) == "a":
                continue
            symbols = operand_symbols(operand, current_global=instruction["parent"], known_symbols=known_symbols)
            contributors.extend(
                contributor(
                    symbol=symbol,
                    relation="value_transform",
                    instruction=instruction,
                    register="a",
                    evidence=f"{instruction['code']} contributes to a",
                    confidence=0.78,
                )
                for symbol in symbols
            )
            pointer = pointer_alias(operand)
            if pointer:
                pointers.add(pointer)
            registers.update(registers_from_operand(operand))

    elif op == "call" and registers:
        symbols = operand_symbols(" ".join(operands), current_global=instruction["parent"], known_symbols=known_symbols)
        contributors.extend(
            contributor(
                symbol=symbol,
                relation="call_transform",
                instruction=instruction,
                register=", ".join(sorted(registers)),
                evidence=f"{instruction['code']} may transform tainted registers",
                confidence=0.46,
            )
            for symbol in symbols
        )

    return expand_registers(registers), expand_registers(pointers), contributors


def last_pointer_assignment(
    register: str,
    instructions: list[dict[str, Any]],
    *,
    current_global: str,
    known_symbols: set[str],
) -> str:
    register = register_name(register)
    for instruction in reversed(instructions[-80:]):
        if instruction["op"] not in {"ld", "ldh"} or len(instruction["operands"]) < 2:
            continue
        destination = register_name(instruction["operands"][0])
        if destination != register:
            continue
        symbols = operand_symbols(
            instruction["operands"][1],
            current_global=current_global or instruction["parent"],
            known_symbols=known_symbols,
        )
        return symbols[0] if symbols else ""
    return ""


def sink_summary(sink: dict[str, Any]) -> dict[str, Any]:
    return {
        "target": sink["target"],
        "routine": sink["routine"],
        "source_file": sink["path"],
        "line": sink["line"],
        "access": sink["access"],
        "code": sink["code"],
        "pointer_register": sink.get("pointer_register", ""),
        "pointer_source": sink.get("pointer_source", ""),
    }


def step_from_sink(sink: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "sink",
        "routine": sink["routine"],
        "source_file": sink["path"],
        "line": sink["line"],
        "op": sink["op"],
        "code": sink["code"],
        "taint": f"{sink['access']} {sink['target']}",
        "contributors": [],
    }


def step_from_instruction(instruction: dict[str, Any], contributors: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "role": "source",
        "routine": instruction["routine"],
        "source_file": instruction["path"],
        "line": instruction["line"],
        "op": instruction["op"],
        "code": instruction["code"],
        "taint": ", ".join(item["symbol"] for item in contributors),
        "contributors": contributors,
    }


def contributor(
    *,
    symbol: str,
    relation: str,
    instruction: dict[str, Any],
    register: str,
    evidence: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "relation": relation,
        "register": register,
        "routine": instruction.get("routine", ""),
        "source_file": instruction.get("path", ""),
        "line": instruction.get("line"),
        "code": instruction.get("code", ""),
        "evidence": evidence,
        "confidence": round(confidence, 3),
    }


def commands_for_target(*, symbol: str, contributors: list[dict[str, Any]]) -> list[str]:
    commands = [
        f"python -m tools.debugger trace-index --symbol {symbol}",
        f"python -m tools.debugger explain --symbol {symbol}",
        f"python -m tools.debugger slice --symbol {symbol}",
        f"python -m tools.debugger replay --symbol {symbol}",
        f"python -m tools.debugger minimize --symbol {symbol}",
    ]
    for contributor_item in contributors[:4]:
        contributor_symbol = contributor_item.get("symbol", "")
        if contributor_symbol and contributor_symbol != symbol:
            commands.append(f"python -m tools.debugger taint --symbol {contributor_symbol}")
            commands.append(f"python -m tools.debugger slice --symbol {contributor_symbol}")
        source_file = contributor_item.get("source_file", "")
        if source_file:
            commands.append(f"python -m tools.debugger slice --source-file {source_file}")
    return unique_list(commands)[:32]


def confidence_for_path(sink: dict[str, Any], contributors: list[dict[str, Any]]) -> float:
    if not contributors:
        return 0.42
    base = 0.7 if sink["access"].startswith("direct") else 0.62
    strongest = max(float(item.get("confidence", 0.0)) for item in contributors)
    return round(min(0.95, base + strongest * 0.2 + min(0.08, len(contributors) * 0.02)), 3)


def split_operands(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    current: list[str] = []
    bracket_depth = 0
    paren_depth = 0
    in_quote = False
    for char in text:
        if char == '"':
            in_quote = not in_quote
        elif not in_quote and char == "[":
            bracket_depth += 1
        elif not in_quote and char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif not in_quote and char == "(":
            paren_depth += 1
        elif not in_quote and char == ")":
            paren_depth = max(0, paren_depth - 1)
        if char == "," and not in_quote and bracket_depth == 0 and paren_depth == 0:
            out.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        out.append("".join(current).strip())
    return [item for item in out if item]


def remove_leading_label(code: str, raw_label: str) -> str:
    stripped = code.lstrip()
    if not stripped.startswith(raw_label):
        return code
    remainder = stripped[len(raw_label):]
    if remainder.startswith("::"):
        return remainder[2:]
    if remainder.startswith(":"):
        return remainder[1:]
    return ""


def operand_mentions_symbol(
    operand: str,
    symbol: str,
    *,
    current_global: str,
    known_symbols: set[str],
) -> bool:
    return symbol in operand_symbols(operand, current_global=current_global, known_symbols=known_symbols)


def operand_symbols(
    operand: str,
    *,
    current_global: str,
    known_symbols: set[str],
) -> list[str]:
    out: list[str] = []
    for token in TOKEN_RE.findall(operand):
        if token in IGNORED_TOKENS or token.lower() in REGISTER_NAMES:
            continue
        resolved = resolve_token(token, current_global=current_global, known_symbols=known_symbols)
        if resolved:
            out.append(resolved)
    return unique_list(out)


def resolve_token(token: str, *, current_global: str, known_symbols: set[str]) -> str:
    if token in known_symbols:
        return token
    if token.startswith(".") and current_global:
        scoped = current_global + token
        if scoped in known_symbols:
            return scoped
    return ""


def registers_from_operands(operands: list[str]) -> set[str]:
    registers: set[str] = set()
    for operand in operands:
        registers.update(registers_from_operand(operand))
    return expand_registers(registers)


def registers_from_operand(operand: str) -> set[str]:
    name = register_name(operand)
    if not name:
        return set()
    return expand_registers({name})


def register_name(operand: str) -> str:
    text = operand.strip().lower()
    if text in REGISTER_NAMES:
        return text
    return ""


def pointer_alias(operand: str) -> str:
    normalized = operand.strip().lower().replace(" ", "")
    return POINTER_ALIASES.get(normalized, "")


def is_memory_operand(operand: str) -> bool:
    text = operand.strip()
    return text.startswith("[") and text.endswith("]")


def expand_registers(registers: set[str]) -> set[str]:
    out: set[str] = set()
    for register in registers:
        if register in REGISTER_PARTS:
            out.add(register)
            out.update(REGISTER_PARTS[register])
        elif register:
            out.add(register)
    return out


def merge_contributors(contributors: Any) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, Any], dict[str, Any]] = {}
    for item in contributors:
        symbol = str(item.get("symbol", ""))
        if not symbol:
            continue
        key = (
            symbol,
            str(item.get("relation", "")),
            str(item.get("source_file", "")),
            item.get("line"),
        )
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["confidence"] = max(float(merged[key]["confidence"]), float(item.get("confidence", 0.0)))
    return sorted(
        merged.values(),
        key=lambda item: (-float(item.get("confidence", 0.0)), str(item.get("symbol", "")), str(item.get("source_file", ""))),
    )


def safe_id(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_")


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
