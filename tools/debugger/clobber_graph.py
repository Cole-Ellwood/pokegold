from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .catalog import ROOT


LABEL_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$?][A-Za-z0-9_.$?]*)(?P<scope>::|:)")
LOCAL_LABEL_ONLY_RE = re.compile(r"^\s*(?P<label>\.[A-Za-z_.$?][A-Za-z0-9_.$?]*)\s*$")
TOKEN_RE = re.compile(r"^\s*(?P<token>[A-Za-z_?][A-Za-z0-9_?]*)\b")

CALL_CONDITIONS = {"z", "nz", "c", "nc"}
FARCALL_MACROS = {"farcall", "callfar", "callba", "callab"}
HOME_CALL_MACROS = {"homecall"}
INDIRECT_TARGETS = {"hl", "(hl)", "[hl]"}
ASM_SOURCE_DIRS = {
    "audio",
    "constants",
    "data",
    "engine",
    "gfx",
    "home",
    "macros",
    "maps",
    "ram",
    "vc",
}
ASM_SOURCE_TOP_LEVEL_FILES = {
    "audio.asm",
    "home.asm",
    "includes.asm",
    "main.asm",
    "ram.asm",
    "rgbdscheck.asm",
}

FARCALL_ABI_CLOBBERS = ("a", "hl")
HOMECALL_ABI_CLOBBERS = ("a",)
FARCALL_ABI_NOTE = (
    "farcall/callfar macro writes a=BANK(target), hl=target before rst FarCall; "
    "home/farcall.asm returns with caller a sourced from target exit c"
)
HOMECALL_ABI_NOTE = (
    "homecall macro bank-switches around a direct call; it restores flags but leaves "
    "a holding the caller's original ROM bank"
)
RST_FARCALL_NOTE = (
    "bare rst FarCall dispatches through a:hl; target must be recovered from the "
    "preceding register setup or runtime trace"
)
RST_JUMPTABLE_NOTE = (
    "rst JumpTable dispatches through a table at hl and ends in jp hl; target is "
    "data-dependent"
)


@dataclass(frozen=True, slots=True)
class AsmLine:
    source_file: str
    line_number: int
    raw: str
    code: str


@dataclass(frozen=True, slots=True)
class FunctionBlock:
    label: str
    parent_label: str
    source_file: str
    line_start: int
    line_end: int
    lines: tuple[AsmLine, ...]

    @property
    def is_local(self) -> bool:
        return self.label != self.parent_label


@dataclass(frozen=True, slots=True)
class CallEdge:
    caller: str
    callee: str | None
    call_type: str
    source_file: str
    line_number: int
    instruction: str
    condition: str | None = None
    resolved: bool = True
    abi_clobbers: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def is_unresolved(self) -> bool:
        return not self.resolved or self.callee is None


@dataclass(frozen=True, slots=True)
class StaticCallGraph:
    root: Path
    source_files: tuple[str, ...]
    blocks: dict[str, FunctionBlock]
    edges: tuple[CallEdge, ...]

    def edges_from(self, caller: str) -> tuple[CallEdge, ...]:
        return tuple(edge for edge in self.edges if edge.caller == caller)

    def unresolved_edges(self) -> tuple[CallEdge, ...]:
        return tuple(edge for edge in self.edges if edge.is_unresolved)

    def reachable_edges(self, start: str, *, max_depth: int = 12) -> tuple[tuple[str, ...], ...]:
        if start not in self.blocks:
            return ()
        chains: list[tuple[str, ...]] = []
        queue: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
        seen: set[tuple[str, str | None]] = set()
        while queue:
            caller, chain = queue.pop(0)
            if len(chain) > max_depth:
                continue
            for edge in self.edges_from(caller):
                key = (edge.caller, edge.callee)
                if key in seen:
                    continue
                seen.add(key)
                if edge.callee is None:
                    chains.append((*chain, "<unresolved>"))
                    continue
                next_chain = (*chain, edge.callee)
                chains.append(next_chain)
                if edge.callee in self.blocks and edge.callee not in chain:
                    queue.append((edge.callee, next_chain))
        return tuple(chains)


class _BlockBuilder:
    def __init__(self, *, label: str, parent_label: str, source_file: str, line_start: int) -> None:
        self.label = label
        self.parent_label = parent_label
        self.source_file = source_file
        self.line_start = line_start
        self.line_end = line_start
        self.lines: list[AsmLine] = []

    def add_line(self, line: AsmLine) -> None:
        self.lines.append(line)
        self.line_end = line.line_number

    def finish(self) -> FunctionBlock:
        return FunctionBlock(
            label=self.label,
            parent_label=self.parent_label,
            source_file=self.source_file,
            line_start=self.line_start,
            line_end=self.line_end,
            lines=tuple(self.lines),
        )


def build_static_call_graph(
    *,
    root: Path = ROOT,
    source_files: Iterable[str | Path] | None = None,
) -> StaticCallGraph:
    root = root.resolve()
    paths = tuple(_resolve_source_files(root=root, source_files=source_files))
    blocks: dict[str, FunctionBlock] = {}
    for path in paths:
        for block in parse_label_blocks(path, root=root):
            blocks[block.label] = block
    edges: list[CallEdge] = []
    for block in blocks.values():
        edges.extend(extract_call_edges(block))
    return StaticCallGraph(
        root=root,
        source_files=tuple(_display_path(path, root=root) for path in paths),
        blocks=blocks,
        edges=tuple(edges),
    )


def build_call_graph_report(
    *,
    function: str | None = None,
    root: Path = ROOT,
    source_files: Iterable[str | Path] | None = None,
) -> dict[str, object]:
    graph = build_static_call_graph(root=root, source_files=source_files)
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "unified_debugger_clobber_call_graph",
        "source_file_count": len(graph.source_files),
        "function_count": len(graph.blocks),
        "edge_count": len(graph.edges),
        "unresolved_edge_count": len(graph.unresolved_edges()),
    }
    if function is None:
        return report
    if function not in graph.blocks:
        report["valid"] = False
        report["errors"] = [f"function label {function!r} was not found"]
        return report
    report["valid"] = True
    report["function"] = function
    report["direct_edges"] = [_edge_to_dict(edge) for edge in graph.edges_from(function)]
    report["reachable_chains"] = [list(chain) for chain in graph.reachable_edges(function)]
    return report


def parse_label_blocks(path: str | Path, *, root: Path = ROOT) -> tuple[FunctionBlock, ...]:
    source_path = Path(path)
    if not source_path.is_absolute():
        source_path = root / source_path
    display = _display_path(source_path, root=root)
    blocks: list[FunctionBlock] = []
    current_global = ""
    builder: _BlockBuilder | None = None

    def finish_builder() -> None:
        nonlocal builder
        if builder is not None:
            blocks.append(builder.finish())
            builder = None

    for line_number, raw in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
        clean = strip_comment(raw)
        if is_block_boundary_directive(clean):
            finish_builder()
            current_global = ""
            continue
        label, code = split_label(clean)
        if label:
            finish_builder()
            if label.startswith("."):
                parent = current_global
                qualified = f"{parent}{label}" if parent else label
            else:
                parent = label
                qualified = label
                current_global = label
            builder = _BlockBuilder(
                label=qualified,
                parent_label=parent or qualified,
                source_file=display,
                line_start=line_number,
            )
            if code:
                builder.add_line(AsmLine(display, line_number, raw, code))
            continue
        if builder is None:
            continue
        if clean.strip():
            builder.add_line(AsmLine(display, line_number, raw, clean.strip()))

    finish_builder()
    return tuple(blocks)


def extract_call_edges(block: FunctionBlock) -> tuple[CallEdge, ...]:
    edges: list[CallEdge] = []
    for line in block.lines:
        edge = parse_call_edge(line, caller=block.label, parent_label=block.parent_label)
        if edge is not None:
            edges.append(edge)
    return tuple(edges)


def parse_call_edge(line: AsmLine, *, caller: str, parent_label: str) -> CallEdge | None:
    code = line.code.strip()
    token = first_token(code).lower()
    if not token:
        return None
    operands = code[len(first_token(code)):].strip()
    args = split_operands(operands)

    if token == "call":
        condition, target = _condition_and_target(args)
        if target is None:
            return None
        return _direct_edge(
            caller=caller,
            target=target,
            parent_label=parent_label,
            call_type="call",
            condition=condition,
            line=line,
        )

    if token == "jp":
        condition, target = _condition_and_target(args)
        if target is None:
            return None
        target_key = _normalize_target_token(target).lower()
        if target_key in INDIRECT_TARGETS:
            return _unresolved_edge(
                caller=caller,
                call_type="indirect_jump",
                line=line,
                notes=("jp hl dispatch target is register-dependent",),
            )
        return _direct_edge(
            caller=caller,
            target=target,
            parent_label=parent_label,
            call_type="jump",
            condition=condition,
            line=line,
        )

    if token in FARCALL_MACROS:
        target = args[0] if args else ""
        return _direct_edge(
            caller=caller,
            target=target,
            parent_label=parent_label,
            call_type="farcall",
            condition=None,
            line=line,
            abi_clobbers=FARCALL_ABI_CLOBBERS,
            notes=(FARCALL_ABI_NOTE,),
        )

    if token in HOME_CALL_MACROS:
        target = args[0] if args else ""
        return _direct_edge(
            caller=caller,
            target=target,
            parent_label=parent_label,
            call_type="homecall",
            condition=None,
            line=line,
            abi_clobbers=HOMECALL_ABI_CLOBBERS,
            notes=(HOMECALL_ABI_NOTE,),
        )

    if token == "rst":
        target = args[0] if args else ""
        target_key = _normalize_target_token(target)
        if target_key == "FarCall":
            return _unresolved_edge(
                caller=caller,
                call_type="rst_farcall",
                line=line,
                abi_clobbers=FARCALL_ABI_CLOBBERS,
                notes=(RST_FARCALL_NOTE, FARCALL_ABI_NOTE),
            )
        if target_key == "JumpTable":
            return _unresolved_edge(
                caller=caller,
                call_type="rst_jumptable",
                line=line,
                notes=(RST_JUMPTABLE_NOTE,),
            )
        if target_key:
            return _direct_edge(
                caller=caller,
                target=target_key,
                parent_label=parent_label,
                call_type="rst",
                condition=None,
                line=line,
            )
    return None


def strip_comment(line: str) -> str:
    out: list[str] = []
    in_quote = False
    escaped = False
    for char in line:
        if char == '"' and not escaped:
            in_quote = not in_quote
        if char == ";" and not in_quote:
            break
        out.append(char)
        escaped = char == "\\" and not escaped
    return "".join(out)


def split_label(line: str) -> tuple[str, str]:
    match = LABEL_RE.match(line)
    if match is not None:
        label = match.group("label")
        return label, line[match.end():].strip()
    match = LOCAL_LABEL_ONLY_RE.match(line)
    if match is not None:
        return match.group("label"), ""
    return "", line.strip()


def first_token(line: str) -> str:
    match = TOKEN_RE.match(line.strip())
    return match.group("token") if match else ""


def is_block_boundary_directive(line: str) -> bool:
    token = first_token(line).upper()
    return token in {"SECTION", "ENDSECTION", "MACRO", "ENDM"}


def split_operands(text: str) -> list[str]:
    if not text:
        return []
    args: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote = False
    escaped = False
    for char in text:
        if char == '"' and not escaped:
            in_quote = not in_quote
        elif not in_quote:
            if char in "([":
                depth += 1
            elif char in ")]" and depth > 0:
                depth -= 1
            elif char == "," and depth == 0:
                args.append("".join(current).strip())
                current = []
                escaped = False
                continue
        current.append(char)
        escaped = char == "\\" and not escaped
    if current:
        args.append("".join(current).strip())
    return [arg for arg in args if arg]


def _condition_and_target(args: list[str]) -> tuple[str | None, str | None]:
    if not args:
        return None, None
    if len(args) >= 2 and args[0].lower() in CALL_CONDITIONS:
        return args[0].lower(), args[1]
    return None, args[0]


def _direct_edge(
    *,
    caller: str,
    target: str,
    parent_label: str,
    call_type: str,
    condition: str | None,
    line: AsmLine,
    abi_clobbers: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> CallEdge | None:
    callee = resolve_target(target, parent_label=parent_label)
    if not callee:
        return None
    return CallEdge(
        caller=caller,
        callee=callee,
        call_type=call_type,
        condition=condition,
        source_file=line.source_file,
        line_number=line.line_number,
        instruction=line.code,
        abi_clobbers=abi_clobbers,
        notes=notes,
    )


def _unresolved_edge(
    *,
    caller: str,
    call_type: str,
    line: AsmLine,
    abi_clobbers: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> CallEdge:
    return CallEdge(
        caller=caller,
        callee=None,
        call_type=call_type,
        source_file=line.source_file,
        line_number=line.line_number,
        instruction=line.code,
        resolved=False,
        abi_clobbers=abi_clobbers,
        notes=notes,
    )


def resolve_target(target: str, *, parent_label: str) -> str:
    name = _normalize_target_token(target)
    if not name:
        return ""
    if name.startswith(".") and parent_label:
        return f"{parent_label}{name}"
    return name


def _normalize_target_token(target: str) -> str:
    text = target.strip()
    if text.startswith("[") and text.endswith("]"):
        return f"[{text[1:-1].strip()}]"
    if text.startswith("(") and text.endswith(")"):
        return f"({text[1:-1].strip()})"
    return text


def _resolve_source_files(
    *,
    root: Path,
    source_files: Iterable[str | Path] | None,
) -> list[Path]:
    if source_files is not None:
        paths = []
        for source in source_files:
            path = Path(source)
            if not path.is_absolute():
                path = root / path
            paths.append(path)
        return paths
    return list(iter_asm_source_files(root=root))


def iter_asm_source_files(*, root: Path = ROOT) -> tuple[Path, ...]:
    root = root.resolve()
    paths: list[Path] = []
    for filename in sorted(ASM_SOURCE_TOP_LEVEL_FILES):
        path = root / filename
        if path.is_file():
            paths.append(path)
    for dirname in sorted(ASM_SOURCE_DIRS):
        directory = root / dirname
        if directory.is_dir():
            paths.extend(sorted(directory.rglob("*.asm")))
    return tuple(paths)


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _edge_to_dict(edge: CallEdge) -> dict[str, object]:
    return {
        "caller": edge.caller,
        "callee": edge.callee,
        "call_type": edge.call_type,
        "source_file": edge.source_file,
        "line_number": edge.line_number,
        "instruction": edge.instruction,
        "condition": edge.condition,
        "resolved": edge.resolved,
        "abi_clobbers": list(edge.abi_clobbers),
        "notes": list(edge.notes),
    }
