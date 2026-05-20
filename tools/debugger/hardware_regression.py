from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .hook_order import build_hook_order_probe_report
from .reporting import load_reports


PAN_DOCS_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "tima_overflow_cycle_a_tima_write_cancels_reload",
        "bucket": "timer",
        "title": "TIMA overflow cycle A write cancels reload and IF request",
        "pan_docs_url": "https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html",
        "required_evidence": "cycle-exact TIMA overflow runtime event with a TIMA write during cycle A",
        "hardware_models": ("timer_tima_overflow",),
        "pyboy_gap_ids": ("pyboy_timer_no_overflow_ab_cycle_model",),
    },
    {
        "id": "tima_overflow_cycle_b_tima_write_ignored",
        "bucket": "timer",
        "title": "TIMA overflow cycle B TIMA write is overwritten by TMA reload",
        "pan_docs_url": "https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html",
        "required_evidence": "cycle-exact TIMA overflow runtime event with a TIMA write during cycle B",
        "hardware_models": ("timer_tima_overflow",),
        "pyboy_gap_ids": ("pyboy_timer_no_overflow_ab_cycle_model",),
    },
    {
        "id": "tima_overflow_cycle_b_tma_write_copies_to_tima",
        "bucket": "timer",
        "title": "TIMA overflow cycle B TMA write also changes the TIMA reload value",
        "pan_docs_url": "https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html",
        "required_evidence": "cycle-exact TIMA overflow runtime event with a TMA write during cycle B",
        "hardware_models": ("timer_tima_overflow",),
        "pyboy_gap_ids": ("pyboy_timer_no_overflow_ab_cycle_model",),
    },
    {
        "id": "oam_dma_160_mcycle_timing",
        "bucket": "dma",
        "title": "FF46 OAM DMA consumes 160 M-cycles before normal CPU access resumes",
        "pan_docs_url": "https://gbdev.io/pandocs/OAM_DMA_Transfer.html",
        "required_evidence": "runtime OAM DMA start/copy/end events with elapsed 160 M-cycles",
        "hardware_models": ("oam_dma",),
        "hook_matrix_row": "oam_dma_ff46",
        "hook_observation": "observes_post_dma",
        "pyboy_gap_ids": ("pyboy_oam_dma_instant_copy_todo",),
    },
    {
        "id": "oam_dma_dmg_ram_access_restricted",
        "bucket": "dma",
        "title": "DMG OAM DMA restricts CPU access to HRAM during the transfer",
        "pan_docs_url": "https://gbdev.io/pandocs/OAM_DMA_Transfer.html",
        "required_evidence": "runtime OAM DMA bus-conflict event proving non-HRAM access is blocked during transfer",
        "hardware_models": ("oam_dma",),
        "hook_matrix_row": "oam_dma_ff46",
        "hook_observation": "observes_post_dma",
        "pyboy_gap_ids": ("pyboy_oam_dma_instant_copy_todo",),
    },
    {
        "id": "cgb_gp_vram_dma_cpu_halt_timing",
        "bucket": "dma",
        "title": "CGB general-purpose VRAM DMA halts CPU until all requested bytes complete",
        "pan_docs_url": "https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma",
        "required_evidence": "runtime FF55 GP DMA event with source/destination/length and elapsed block timing",
        "hardware_models": ("cgb_vram_dma",),
        "hook_matrix_row": "cgb_vram_dma_ff55",
        "hook_observation": "observes_post_dma",
        "pyboy_gap_ids": ("pyboy_gpdma_cycles_todo",),
    },
    {
        "id": "cgb_hblank_vram_dma_block_timing",
        "bucket": "dma",
        "title": "CGB HBlank VRAM DMA transfers one 16-byte block per HBlank with correct speed timing",
        "pan_docs_url": "https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma",
        "required_evidence": "runtime HBlank DMA block events tied to LCD mode 0 and double-speed timing",
        "hardware_models": ("cgb_vram_dma", "lcd_mode_edge"),
        "pyboy_gap_ids": ("pyboy_hdma_double_speed_todo", "pyboy_lcd_fixed_bucket_modes"),
    },
    {
        "id": "interrupt_entry_stack_writes_current_pc",
        "bucket": "interrupt",
        "title": "Interrupt entry pushes the current PC to the stack before jumping to the vector",
        "pan_docs_url": "https://gbdev.io/pandocs/Interrupts.html",
        "required_evidence": "runtime interrupt_enter and stack_write events with vector, SP, and pushed PC",
        "hardware_models": ("interrupt_entry",),
        "hook_matrix_row": "interrupt_entry",
        "hook_observation": "observes_post_interrupt",
        "pyboy_gap_ids": ("pyboy_hook_opcode_breakpoint_model",),
    },
    {
        "id": "boot_rom_pokemon_gold_end_state",
        "bucket": "bootrom",
        "title": "Real boot ROM plus Pokemon Gold reaches documented CGB/DMG post-boot CPU and register state",
        "pan_docs_url": "https://gbdev.io/pandocs/Power_Up_Sequence.html",
        "required_evidence": "runtime boot-ROM execution with real boot ROM artifact, Pokemon Gold ROM hash, and post-boot register/IO state",
        "hardware_models": ("boot_rom_end_state",),
        "pyboy_gap_ids": (),
        "requires_bootrom": True,
    },
    {
        "id": "lcd_dot_mode_edge_timing",
        "bucket": "ppu",
        "title": "LCD mode edges and memory access restrictions match dot-level rendering timing",
        "pan_docs_url": "https://gbdev.io/pandocs/Rendering.html",
        "required_evidence": "runtime LCD mode-edge events with dot position, mode, and VRAM/OAM accessibility",
        "hardware_models": ("lcd_mode_edge", "ppu_lcd_mode"),
        "pyboy_gap_ids": ("pyboy_lcd_fixed_bucket_modes",),
    },
)


PYBOY_SOURCE_GAPS: tuple[dict[str, Any], ...] = (
    {
        "id": "pyboy_hook_opcode_breakpoint_model",
        "path": "pyboy.py",
        "needles": (
            "PC has not been incremented when hitting breakpoint",
            "Hooks are installed by replacing the instruction",
            "opcode (`0xDB`)",
        ),
        "summary": "PyBoy hooks are opcode-replacement breakpoints, not non-mutating CPU events.",
    },
    {
        "id": "pyboy_oam_dma_instant_copy_todo",
        "path": "core/mb.py",
        "needles": (
            "def transfer_DMA",
            "TODO: Add timing delay of 160",
            "disallow access to RAM",
        ),
        "summary": "PyBoy OAM DMA copies immediately and has a TODO for timing/RAM access restrictions.",
    },
    {
        "id": "pyboy_gpdma_cycles_todo",
        "path": "core/mb.py",
        "needles": (
            "General purpose DMA transfer",
            "TODO: Progress cpu cycles",
        ),
        "summary": "PyBoy CGB general-purpose VRAM DMA has a TODO for CPU-cycle progress.",
    },
    {
        "id": "pyboy_hdma_double_speed_todo",
        "path": "core/mb.py",
        "needles": (
            "return 206",
            "TODO: adjust for double speed",
        ),
        "summary": "PyBoy HBlank DMA returns a fixed cycle cost with a double-speed TODO.",
    },
    {
        "id": "pyboy_lcd_fixed_bucket_modes",
        "path": "core/lcd.py",
        "needles": (
            "mode2 = 80",
            "mode3 = 170",
            "self.clock_target += 206",
        ),
        "summary": "PyBoy LCD mode timing is bucketed, not a dot-level FIFO proof model.",
    },
    {
        "id": "pyboy_timer_no_overflow_ab_cycle_model",
        "path": "core/timer.py",
        "needles": (
            "if self.TIMA > 0xFF",
            "self.TIMA = self.TMA",
        ),
        "summary": "PyBoy timer reload is modeled directly, without the Pan Docs TIMA overflow A/B-cycle write semantics.",
    },
)


EXPLICIT_HARDWARE_EVIDENCE = {
    "emulator_hardware_event",
    "hardware_event_observed",
    "non_mutating_event_recorder",
    "runtime_hardware_event_observed",
}


def build_hardware_regression_report(
    *,
    reports: tuple[str, ...] = (),
    execute: bool = False,
    bootrom: str = "",
    rom_path: str = "pokegold.gbc",
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    generated_reports: list[dict[str, Any]] = []
    warnings: list[str] = []
    if execute:
        hook_order = build_hook_order_probe_report(execute=True, root=root)
        generated_reports.append({"source": "<executed-hook-order-probe>", "data": hook_order})
        if not hook_order.get("valid"):
            warnings.extend(str(error) for error in hook_order.get("errors", []))

    all_reports = [*loaded_reports, *generated_reports]
    pyboy_source_gaps = scan_pyboy_source_gaps()
    bootrom_path = resolve_path(bootrom, root=root) if bootrom else None
    rom = resolve_path(rom_path, root=root) if rom_path else None
    cases = [
        build_case_result(
            case,
            reports=all_reports,
            pyboy_source_gaps=pyboy_source_gaps,
            bootrom_path=bootrom_path,
            rom_path=rom,
            root=root,
        )
        for case in PAN_DOCS_CASES
    ]
    blocking_cases = [case for case in cases if not case["hardware_passed"]]
    status_counts = count_by(cases, "gate_status")
    pyboy_gap_count = sum(1 for gap in pyboy_source_gaps if gap["present"])
    errors = list(load_errors)
    return {
        "schema_version": 1,
        "kind": "unified_debugger_hardware_regression_gate",
        "root": str(root),
        "valid": not errors,
        "passed": not errors and not blocking_cases,
        "proof_status": "runtime_observed" if not errors and not blocking_cases else "planned_only",
        "hardware_behavior_proven": not errors and not blocking_cases,
        "executed": execute,
        "case_count": len(cases),
        "passed_count": len(cases) - len(blocking_cases),
        "blocking_gate_count": len(blocking_cases),
        "case_status_counts": status_counts,
        "pyboy_source_gap_count": pyboy_gap_count,
        "pyboy_source_gaps": pyboy_source_gaps,
        "reports": list(reports),
        "generated_report_count": len(generated_reports),
        "generated_reports": [
            {
                "source": str(item["source"]),
                "kind": str(item["data"].get("kind", "")),
                "valid": bool(item["data"].get("valid", False)),
                "passed": bool(item["data"].get("passed", False)),
            }
            for item in generated_reports
        ],
        "bootrom": display_path(bootrom_path, root=root) if bootrom_path else "",
        "bootrom_present": bool(bootrom_path and bootrom_path.exists()),
        "rom": display_path(rom, root=root) if rom else "",
        "rom_present": bool(rom and rom.exists()),
        "cases": cases,
        "blocking_cases": [case["id"] for case in blocking_cases],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "commands": [
            "python -m tools.debugger hardware-regression-gate --execute",
            "python -m tools.debugger hook-order-probe --execute",
        ],
        "known_limits": [
            "This gate is intentionally strict: PyBoy hook observations and modeled effect traces do not satisfy Pan Docs hardware cases by themselves.",
            "A case passes only when explicit hardware-event evidence or a dedicated hardware-regression result marks that exact case passed.",
            "Boot-ROM end-state proof needs a real boot ROM artifact and Pokemon Gold ROM runtime evidence; file presence alone is not enough.",
        ],
    }


def build_case_result(
    case: dict[str, Any],
    *,
    reports: list[dict[str, Any]],
    pyboy_source_gaps: list[dict[str, Any]],
    bootrom_path: Path | None,
    rom_path: Path | None,
    root: Path,
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    for gap_id in case.get("pyboy_gap_ids", ()):
        gap = next((item for item in pyboy_source_gaps if item["id"] == gap_id), None)
        if gap and gap["present"]:
            evidence.append(
                {
                    "class": "pyboy_source_gap",
                    "status": "blocking",
                    "source": gap["source"],
                    "detail": gap["summary"],
                }
            )

    for loaded in reports:
        report = loaded.get("data", {})
        source = str(loaded.get("source", ""))
        evidence.extend(report_case_evidence(case, report, source=source))

    if case.get("requires_bootrom"):
        if not bootrom_path or not bootrom_path.exists():
            evidence.append(
                {
                    "class": "missing_artifact",
                    "status": "blocking",
                    "source": display_path(bootrom_path, root=root) if bootrom_path else "<bootrom>",
                    "detail": "real boot ROM artifact is required for this gate",
                }
            )
        if not rom_path or not rom_path.exists():
            evidence.append(
                {
                    "class": "missing_artifact",
                    "status": "blocking",
                    "source": display_path(rom_path, root=root) if rom_path else "<rom>",
                    "detail": "Pokemon Gold ROM artifact is required for this gate",
                }
            )

    hardware_passed = any(item["class"] == "explicit_hardware_case_pass" for item in evidence)
    if hardware_passed:
        gate_status = "passed"
        proof_status = "runtime_observed"
    elif any(item["class"] == "pyboy_hook_matrix" for item in evidence):
        gate_status = "emulator_observed_not_hardware"
        proof_status = "planned_only"
    elif any(item["class"] == "pyboy_source_gap" for item in evidence):
        gate_status = "blocked_pyboy_fidelity_gap"
        proof_status = "planned_only"
    elif any(item["class"] == "missing_artifact" for item in evidence):
        gate_status = "missing_artifact"
        proof_status = "planned_only"
    else:
        gate_status = "missing_runtime_hardware_evidence"
        proof_status = "planned_only"

    return {
        "id": case["id"],
        "bucket": case["bucket"],
        "title": case["title"],
        "pan_docs_url": case["pan_docs_url"],
        "required_evidence": case["required_evidence"],
        "hardware_models": list(case.get("hardware_models", ())),
        "hardware_passed": hardware_passed,
        "hardware_behavior_proven": hardware_passed,
        "gate_status": gate_status,
        "proof_status": proof_status,
        "evidence_count": len(evidence),
        "evidence": evidence,
    }


def report_case_evidence(case: dict[str, Any], report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    if report.get("valid", True) is False:
        return [
            {
                "class": "invalid_report",
                "status": "ignored",
                "source": source,
                "detail": "invalid hardware evidence report cannot satisfy a Pan Docs gate",
            }
        ]
    evidence: list[dict[str, Any]] = []
    evidence.extend(explicit_case_result_evidence(case, report, source=source))
    evidence.extend(hook_order_case_evidence(case, report, source=source))
    evidence.extend(effect_trace_case_evidence(case, report, source=source))
    return evidence


def explicit_case_result_evidence(case: dict[str, Any], report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in [*dict_items(report.get("cases")), *dict_items(report.get("hardware_regression_cases"))]:
        if str(item.get("id", "")) != case["id"]:
            continue
        declared_pass = bool(item.get("hardware_passed") or item.get("passed"))
        passed = declared_pass and explicit_case_item_hardware_proven(item)
        if declared_pass and not passed:
            status = "declared_pass_without_hardware_proof"
            detail = (
                str(item.get("detail") or item.get("title") or case["title"])
                + "; ignored as a hardware pass because hardware_behavior_proven=true is missing"
            )
        else:
            status = "passed" if passed else str(item.get("gate_status", "not_passed"))
            detail = str(item.get("detail") or item.get("title") or case["title"])
        out.append(
            {
                "class": "explicit_hardware_case_pass" if passed else "explicit_hardware_case_result",
                "status": status,
                "source": source,
                "detail": detail,
            }
        )
    for case_id in string_items(report.get("hardware_regression_case_ids")):
        if case_id == case["id"] and bool(report.get("hardware_behavior_proven")):
            out.append(
                {
                    "class": "explicit_hardware_case_pass",
                    "status": "passed",
                    "source": source,
                    "detail": "report declares hardware_behavior_proven for this case id",
                }
            )
    if (
        str(report.get("hardware_regression_case_id", "")) == case["id"]
        and bool(report.get("hardware_behavior_proven"))
    ):
        out.append(
            {
                "class": "explicit_hardware_case_pass",
                "status": "passed",
                "source": source,
                "detail": "report declares hardware_behavior_proven for this case id",
            }
        )
    return out


def explicit_case_item_hardware_proven(item: dict[str, Any]) -> bool:
    if item.get("hardware_behavior_proven") is True:
        return True
    if item.get("hardware_event_observed") is True:
        return True
    proof_status = str(item.get("proof_status") or "")
    evidence_source = str(item.get("evidence_source") or "")
    evidence_status = str(item.get("evidence_status") or "")
    return (
        proof_status in EXPLICIT_HARDWARE_EVIDENCE
        or evidence_source in EXPLICIT_HARDWARE_EVIDENCE
        or evidence_status in EXPLICIT_HARDWARE_EVIDENCE
    )


def hook_order_case_evidence(case: dict[str, Any], report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    if report.get("kind") != "unified_debugger_hook_order_probe":
        return []
    row_id = str(case.get("hook_matrix_row", ""))
    observation = str(case.get("hook_observation", ""))
    if not row_id or not observation:
        return []
    row = next((item for item in dict_items(report.get("event_matrix")) if str(item.get("id", "")) == row_id), None)
    if not row or not row.get(observation):
        return []
    return [
        {
            "class": "pyboy_hook_matrix",
            "status": "emulator_observed_not_hardware",
            "source": source,
            "detail": f"{row_id}.{observation}=true; hook matrix is not non-mutating hardware-event evidence",
        }
    ]


def effect_trace_case_evidence(case: dict[str, Any], report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    if report.get("kind") != "unified_debugger_effect_trace":
        return []
    models = set(str(item) for item in case.get("hardware_models", ()))
    out: list[dict[str, Any]] = []
    for event in dict_items(report.get("events")):
        for item in dict_items(event.get("effects")):
            model = str(item.get("hardware_model", ""))
            if model not in models:
                continue
            runtime_event = hardware_runtime_event_present(item)
            out.append(
                {
                    "class": "runtime_hardware_event" if runtime_event else "modeled_effect_trace",
                    "status": (
                        "runtime_event_present_not_case_complete"
                        if runtime_event
                        else str(item.get("hardware_proof_gate", "modeled_only"))
                    ),
                    "source": source,
                    "detail": f"{model} seq={event.get('seq', '')} kind={item.get('kind', '')}",
                }
            )
    return out


def hardware_runtime_event_present(item: dict[str, Any]) -> bool:
    return bool(
        item.get("hardware_runtime_event")
        or str(item.get("hardware_proof_gate", "")) == "explicit_runtime_event_present"
        or str(item.get("evidence_source", "")) in EXPLICIT_HARDWARE_EVIDENCE
        or str(item.get("evidence_status", "")) in EXPLICIT_HARDWARE_EVIDENCE
        or str(item.get("runtime_observation", "")) in EXPLICIT_HARDWARE_EVIDENCE
    )


def scan_pyboy_source_gaps() -> list[dict[str, Any]]:
    base = pyboy_package_base()
    out: list[dict[str, Any]] = []
    for gap in PYBOY_SOURCE_GAPS:
        path = base / gap["path"] if base else None
        text = ""
        if path and path.exists():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
        present = bool(text) and all(needle in text for needle in gap["needles"])
        out.append(
            {
                "id": gap["id"],
                "present": present,
                "status": "gap_present" if present else "not_found",
                "source": str(path) if path else "<pyboy-not-installed>",
                "summary": gap["summary"],
            }
        )
    return out


def pyboy_package_base() -> Path | None:
    spec = importlib.util.find_spec("pyboy")
    if not spec or not spec.origin:
        return None
    return Path(spec.origin).parent


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def string_items(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return counts


def resolve_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_path(path: Path | None, *, root: Path) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
