#!/usr/bin/env python3
"""Audit queued VRAM tile-request contracts.

This guards the graphics race found after late-VBlank request guards were added:
Request1bpp/Request2bpp must not treat a queued copy as complete until the
VBlank service routine clears the request-size byte. A single DelayFrame is not
enough, because a late VBlank can intentionally skip the copy.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from asm_scan import LOCAL_LABEL_RE, ROOT, TOP_LABEL_RE, code_part
except ModuleNotFoundError:  # pragma: no cover - import path when used as a module
    from tools.audit.asm_scan import LOCAL_LABEL_RE, ROOT, TOP_LABEL_RE, code_part


GFX_PATH = ROOT / "home" / "gfx.asm"
VIDEO_PATH = ROOT / "home" / "video.asm"
VBLANK_PATH = ROOT / "home" / "vblank.asm"


@dataclass(frozen=True)
class CodeLine:
    lineno: int
    text: str
    raw: str


@dataclass(frozen=True)
class Issue:
    path: Path
    lineno: int
    reason: str
    line: str = ""


def code_lines(lines: list[str]) -> list[CodeLine]:
    out: list[CodeLine] = []
    for lineno, raw in enumerate(lines, start=1):
        code = code_part(raw)
        if code:
            out.append(CodeLine(lineno=lineno, text=code, raw=raw.rstrip()))
    return out


def global_block(path: Path, lines: list[str], label: str) -> tuple[int, list[CodeLine]] | None:
    entries = code_lines(lines)
    block: list[CodeLine] = []
    in_block = False
    start_lineno = 1

    for entry in entries:
        label_match = TOP_LABEL_RE.match(entry.text)
        if label_match:
            current_label = label_match.group("label")
            if current_label == label:
                in_block = True
                start_lineno = entry.lineno
                continue
            if in_block:
                break
        if in_block:
            block.append(entry)

    if not in_block:
        return None
    return start_lineno, block


def local_label_name(text: str) -> str | None:
    match = LOCAL_LABEL_RE.match(text)
    if not match:
        return None
    return match.group("label")


def local_block(entries: list[CodeLine], label: str) -> tuple[int, int] | None:
    start: int | None = None
    for index, entry in enumerate(entries):
        if local_label_name(entry.text) == label:
            start = index
            break
    if start is None:
        return None
    end = len(entries)
    for index in range(start + 1, len(entries)):
        if local_label_name(entries[index].text):
            end = index
            break
    return start, end


def require_ordered(
    entries: list[CodeLine],
    sequence: tuple[str, ...],
    *,
    path: Path,
    lineno: int,
    reason: str,
    issues: list[Issue],
) -> None:
    index = 0
    for entry in entries:
        if entry.text == sequence[index]:
            index += 1
            if index == len(sequence):
                return
    issues.append(Issue(path=path, lineno=lineno, reason=reason))


def audit_request_block(path: Path, lines: list[str], label: str, size_symbol: str) -> list[Issue]:
    issues: list[Issue] = []
    block = global_block(path, lines, label)
    if block is None:
        return [Issue(path=path, lineno=1, reason=f"{label} is missing")]
    start_lineno, entries = block
    store_text = f"ld [{size_symbol}], a"
    store_indexes = [index for index, entry in enumerate(entries) if entry.text == store_text]
    if not store_indexes:
        issues.append(Issue(path=path, lineno=start_lineno, reason=f"{label} never queues {size_symbol}"))

    wait_range = local_block(entries, ".wait_request")
    if wait_range is None:
        issues.append(Issue(path=path, lineno=start_lineno, reason=f"{label} is missing .wait_request"))
        wait_indexes: set[int] = set()
    else:
        wait_start, wait_end = wait_range
        wait_indexes = set(range(wait_start, wait_end))
        wait_entries = entries[wait_start:wait_end]
        require_ordered(
            wait_entries,
            (
                "call DelayFrame",
                f"ld a, [{size_symbol}]",
                "and a",
                "jr nz, .wait_request",
                "ret",
            ),
            path=path,
            lineno=entries[wait_start].lineno,
            reason=f"{label}.wait_request must loop until {size_symbol} is cleared by VBlank",
            issues=issues,
        )

    for store_index in store_indexes:
        next_index = store_index + 1
        next_text = entries[next_index].text if next_index < len(entries) else "<end of block>"
        if next_text != "call .wait_request":
            issues.append(
                Issue(
                    path=path,
                    lineno=entries[store_index].lineno,
                    reason=(
                        f"{label} queues {size_symbol} but does not immediately call .wait_request "
                        f"(next code: {next_text})"
                    ),
                    line=entries[store_index].raw,
                )
            )

    for index, entry in enumerate(entries):
        if entry.text == "call DelayFrame" and index not in wait_indexes:
            issues.append(
                Issue(
                    path=path,
                    lineno=entry.lineno,
                    reason=f"{label} must wait through .wait_request, not a bare DelayFrame",
                    line=entry.raw,
                )
            )
    return issues


def audit_serve_guard(path: Path, lines: list[str], label: str, size_symbol: str) -> list[Issue]:
    issues: list[Issue] = []
    block = global_block(path, lines, label)
    if block is None:
        return [Issue(path=path, lineno=1, reason=f"{label} is missing")]
    start_lineno, entries = block
    require_ordered(
        entries,
        (
            f"ld a, [{size_symbol}]",
            "and a",
            "ret z",
            "ldh a, [rLY]",
            "cp LY_VBLANK",
            "ret c",
            "cp LY_VBLANK + 2",
            "ret nc",
        ),
        path=path,
        lineno=start_lineno,
        reason=f"{label} must keep the late-VBlank rLY guard before copying tiles",
        issues=issues,
    )
    return issues


def audit_serve_clear(path: Path, lines: list[str], label: str, size_symbol: str) -> list[Issue]:
    issues: list[Issue] = []
    block = global_block(path, lines, label)
    if block is None:
        return [Issue(path=path, lineno=1, reason=f"{label} is missing")]
    start_lineno, entries = block
    require_ordered(
        entries,
        (
            f"ld a, [{size_symbol}]",
            "ld b, a",
            "xor a",
            f"ld [{size_symbol}], a",
        ),
        path=path,
        lineno=start_lineno,
        reason=f"{label} must clear {size_symbol} as the VBlank acknowledgement",
        issues=issues,
    )
    return issues


def audit_vblank_cutscene(path: Path, lines: list[str]) -> list[Issue]:
    block = global_block(path, lines, "VBlank_Cutscene")
    if block is None:
        return [Issue(path=path, lineno=1, reason="VBlank_Cutscene is missing")]
    start_lineno, entries = block
    issues: list[Issue] = []
    require_ordered(
        entries,
        ("call Serve2bppRequest_VBlank",),
        path=path,
        lineno=start_lineno,
        reason="VBlank_Cutscene must use the VBlank-only 2bpp service entry",
        issues=issues,
    )
    return issues


def audit_sources(
    *,
    gfx_lines: list[str],
    video_lines: list[str],
    vblank_lines: list[str],
    gfx_path: Path = GFX_PATH,
    video_path: Path = VIDEO_PATH,
    vblank_path: Path = VBLANK_PATH,
) -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(audit_request_block(gfx_path, gfx_lines, "Request2bpp", "wRequested2bppSize"))
    issues.extend(audit_request_block(gfx_path, gfx_lines, "Request1bpp", "wRequested1bppSize"))
    issues.extend(audit_serve_guard(video_path, video_lines, "Serve2bppRequest", "wRequested2bppSize"))
    issues.extend(audit_serve_clear(video_path, video_lines, "Serve2bppRequest_VBlank", "wRequested2bppSize"))
    issues.extend(audit_serve_guard(video_path, video_lines, "Serve1bppRequest", "wRequested1bppSize"))
    issues.extend(audit_serve_clear(video_path, video_lines, "Serve1bppRequest", "wRequested1bppSize"))
    issues.extend(audit_vblank_cutscene(vblank_path, vblank_lines))
    return issues


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def print_issues(issues: list[Issue]) -> None:
    for issue in issues:
        location = f"{relative_path(issue.path)}:{issue.lineno}"
        print(f"{location}: {issue.reason}")
        if issue.line:
            print(f"    {issue.line}")


def run_self_test() -> int:
    good_gfx = """
Request2bpp::
	ld [wRequested2bppSize], a
	call .wait_request
.cycle
	ld [wRequested2bppSize], a
	call .wait_request
.wait_request
	call DelayFrame
	ld a, [wRequested2bppSize]
	and a
	jr nz, .wait_request
	ret
Request1bpp::
	ld [wRequested1bppSize], a
	call .wait_request
.cycle
	ld [wRequested1bppSize], a
	call .wait_request
.wait_request
	call DelayFrame
	ld a, [wRequested1bppSize]
	and a
	jr nz, .wait_request
	ret
""".strip().splitlines()
    good_video = """
Serve1bppRequest::
	ld a, [wRequested1bppSize]
	and a
	ret z
	ldh a, [rLY]
	cp LY_VBLANK
	ret c
	cp LY_VBLANK + 2
	ret nc
	ld a, [wRequested1bppSize]
	ld b, a
	xor a
	ld [wRequested1bppSize], a
	ret
Serve2bppRequest::
	ld a, [wRequested2bppSize]
	and a
	ret z
	ldh a, [rLY]
	cp LY_VBLANK
	ret c
	cp LY_VBLANK + 2
	ret nc
Serve2bppRequest_VBlank::
	ld a, [wRequested2bppSize]
	and a
	ret z
	ld a, [wRequested2bppSize]
	ld b, a
	xor a
	ld [wRequested2bppSize], a
	ret
""".strip().splitlines()
    good_vblank = """
VBlank_Cutscene::
	call Serve2bppRequest_VBlank
	ret
""".strip().splitlines()
    good_issues = audit_sources(
        gfx_lines=good_gfx,
        video_lines=good_video,
        vblank_lines=good_vblank,
        gfx_path=Path("self_test_gfx.asm"),
        video_path=Path("self_test_video.asm"),
        vblank_path=Path("self_test_vblank.asm"),
    )
    if good_issues:
        print("FAIL: good fixture produced issues")
        print_issues(good_issues)
        return 1

    bad_gfx = list(good_gfx)
    bad_gfx[2] = "\tcall DelayFrame"
    bad_issues = audit_sources(
        gfx_lines=bad_gfx,
        video_lines=good_video,
        vblank_lines=good_vblank,
        gfx_path=Path("self_test_gfx.asm"),
        video_path=Path("self_test_video.asm"),
        vblank_path=Path("self_test_vblank.asm"),
    )
    if not any("does not immediately call .wait_request" in issue.reason for issue in bad_issues):
        print("FAIL: bad fixture did not catch bare DelayFrame after queued request")
        print_issues(bad_issues)
        return 1

    print("PASS: VRAM request contract self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true", help="run in-memory good/bad fixture checks")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    issues = audit_sources(
        gfx_lines=read_lines(GFX_PATH),
        video_lines=read_lines(VIDEO_PATH),
        vblank_lines=read_lines(VBLANK_PATH),
    )
    if issues:
        print_issues(issues)
        print(f"\nFAIL: {len(issues)} VRAM request contract issue(s) detected")
        return 1
    print("PASS: queued VRAM tile requests wait for VBlank acknowledgement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
