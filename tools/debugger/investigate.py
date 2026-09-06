from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid
from itertools import zip_longest
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .clobber_graph import build_static_call_graph
from .content_mirror import build_content_mirror_report
from .content_scenarios import build_content_scenario_report
from .coverage import build_coverage_report, load_traces
from .dynamic_taint import _register_transport
from .expect import build_expectation_report, load_expectation_files, parse_cli_expectation
from .effect_trace import build_effect_trace_report
from .evidence import evidence_atom
from .explain import build_explanation_report
from .fuzz import build_fuzz_plan
from .generate import build_generation_plan
from .impact import build_impact_report
from .ingest import ingest_artifacts
from .instruction_trace import build_instruction_trace_report, is_traceable_function, is_watch_symbol
from .instruction_frames import trace_records
from .localize import build_localization_plan
from .minimize import build_minimization_plan
from .mirrors import build_compare_plan
from .next_steps import build_next_step, symptom_only_investigation_note
from .provenance import build_source_mapping_report, parse_symbol_table, resolve_path
from .report_envelope import replay_state_basis, sha256_file, source_manifest_hash
from .ranking import rank_findings
from .replay import build_replay_plan
from .reporting import _with_hypothesis_overview, build_static_report, write_static_report
from .runtime_state import build_runtime_state_report
from .runtime_experiment import run_runtime_experiment
from .save_state_format import is_vbam_sgm_path
from .save_state_inspect import build_save_state_inspection_report
from .state_space import build_state_space_report
from .slicing import DATA_OPS, LINE_OPS, TOKEN_RE
from .sm83_model import CONDITIONAL_JUMPS, CONDITIONAL_RETS
from .taint import build_taint_report
from .trace_index import build_trace_index_report, unique_list
from .visualization import build_visualization_report, write_visualization
from .workflow import command_is_runnable


DEFAULT_OUT_DIR = ".local\\tmp\\debugger_investigation"


def build_investigation_run(
    *,
    rom_path: str = "",
    symbols_path: str = "pokegold.sym",
    save_state: str = "",
    traces: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    patches: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    rules: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    expectations: tuple[str, ...] = (),
    expectation_files: tuple[str, ...] = (),
    families: tuple[str, ...] = (),
    symptom: str = "",
    out_dir: str = DEFAULT_OUT_DIR,
    execute_watch: bool = False,
    frames: int = 300,
    context_frames: int = 12,
    max_targets: int = 24,
    max_events: int = 1000,
    max_cases: int = 64,
    seed: int = 1,
    root: Path = ROOT,
) -> dict[str, Any]:
    source_basis = source_manifest_hash(root)
    output_dir = resolve_output_dir(out_dir, root=root)
    steps: list[dict[str, Any]] = []
    produced_reports: list[dict[str, Any]] = []
    report_paths = list(reports)
    investigation_evidence = []
    symptom_only_next_step: dict[str, Any] | None = None
    symptom_only_next_step_note = ""

    ingest = ingest_artifacts(
        roms=(rom_path or "pokegold.gbc",) if rom_path or execute_watch else (),
        symbols=(symbols_path,) if symbols_path else (),
        traces=traces,
        save_states=(save_state,) if save_state else (),
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="01_ingest",
        phase="ingest",
        title="Ingest artifacts",
        data=ingest,
        output_dir=output_dir,
        root=root,
    )

    if symptom and not investigation_has_anchor(
        rom_path=rom_path,
        save_state=save_state,
        traces=traces,
        scenarios=scenarios,
        reports=reports,
        patches=patches,
        changed_files=changed_files,
        symbols=symbols,
        watch_symbols=watch_symbols,
        rules=rules,
        addresses=addresses,
        expectations=expectations,
        expectation_files=expectation_files,
        families=families,
    ):
        symptom_only_next_step = build_next_step(symptom=symptom, root=root)
        symptom_only_next_step_note = symptom_only_investigation_note(
            {"symptom": symptom},
            next_step=symptom_only_next_step,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="01_next_step",
            phase="triage",
            title="Route symptom-only next proof path",
            data=symptom_only_next_step,
            output_dir=output_dir,
            root=root,
        )

    if save_state:
        if is_vbam_sgm_path(save_state):
            save_state_inspection = build_save_state_inspection_report(
                save_state=save_state,
                rom_path=rom_path or "pokegold.gbc",
                symbols_path=symbols_path,
                root=root,
            )
            add_report(
                steps,
                produced_reports,
                report_paths,
                step_id="02_save_state_inspect",
                phase="observe",
                title="Decode VBA-M save state",
                data=save_state_inspection,
                output_dir=output_dir,
                root=root,
            )
        runtime_state = build_runtime_state_report(
            rom_path=rom_path or "pokegold.gbc",
            symbols_path=symbols_path,
            save_state=save_state,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="02_runtime_state",
            phase="observe",
            title="Inspect runtime state invariants",
            data=runtime_state,
            output_dir=output_dir,
            root=root,
        )
    else:
        add_skipped_step(
            steps,
            step_id="02_runtime_state",
            phase="observe",
            title="Inspect runtime state invariants",
            reason="no save state was supplied",
        )

    effective_watch_symbols = watch_symbols
    if patches:
        state_space_out_state = (
            display_output_path(output_dir / "state_space_patched.state", root=root)
            if output_dir and save_state else ""
        )
        state_space_report_path = (
            display_output_path(output_dir / "02_state_space.json", root=root)
            if output_dir else ""
        )
        state_space = build_state_space_report(
            patches=patches,
            watch_symbols=watch_symbols,
            scenario_id="investigation_state_space_1",
            source_files=changed_files,
            symptom=symptom,
            rom_path=rom_path or "pokegold.gbc",
            symbols_path=symbols_path,
            base_save_state=save_state,
            out_state=state_space_out_state,
            execute=False,
            report_path=state_space_report_path,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="02_state_space",
            phase="observe",
            title="Build generic state-space patch report",
            data=state_space,
            output_dir=output_dir,
            root=root,
        )
        effective_watch_symbols = tuple(
            unique_list([*watch_symbols, *string_items(state_space.get("watch_symbols"))])
        )

    trace_index = build_trace_index_report(
        traces=traces,
        reports=tuple(report_paths),
        symbols=symbols,
        watch_symbols=effective_watch_symbols,
        addresses=addresses,
        rules=rules,
        source_files=changed_files,
        symptom=symptom,
        symbols_path=symbols_path,
        max_events=max_events,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="02_trace_index",
        phase="observe",
        title="Build trace evidence index",
        data=trace_index,
        output_dir=output_dir,
        root=root,
    )

    content_files = content_mirror_files(changed_files, root=root)
    if content_files:
        content_scenarios = build_content_scenario_report(
            changed_files=content_files,
            out_scenarios=display_output_path(output_dir / "content_scenarios.jsonl", root=root) if output_dir else "",
            max_cases=max_cases,
            seed=seed,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="02_content_scenarios",
            phase="observe",
            title="Generate content semantic scenarios",
            data=content_scenarios,
            output_dir=output_dir,
            root=root,
        )

    requested, expectation_errors = load_expectation_files(expectation_files=expectation_files, root=root)
    requested.extend(parse_cli_expectation(value) for value in expectations)
    expected_watches = unique_list(
        item.get("state_symbol") or item.get("symbol") for item in requested
        if item.get("event_type") == "memory_read"
        and item.get("operation") in ("baseline.initial", "baseline.final")
        and (item.get("state_symbol") or item.get("symbol"))
    )
    expected_points = unique_list(
        item["pc_symbol"] for item in requested
        if item.get("event_type") == "control_flow"
        and str(item.get("operation", "")).startswith("baseline.checkpoint.")
        and item.get("pc_symbol")
    )
    replay = build_replay_plan(
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        traces=traces,
        scenarios=scenarios,
        reports=tuple(report_paths),
        watch_symbols=tuple(unique_list([*effective_watch_symbols, *expected_watches])),
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        frames=frames,
        context_frames=context_frames,
        execute_watch=execute_watch,
        max_targets=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="03_replay",
        phase="reproduce",
        title="Build replay plan",
        data=replay,
        output_dir=output_dir,
        root=root,
    )

    localize = build_localization_plan(
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        reports=tuple(report_paths),
        symbols_path=symbols_path,
        max_candidates=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="04_localize",
        phase="localize",
        title="Localize suspects",
        data=localize,
        output_dir=output_dir,
        root=root,
    )

    expectation_baseline = None
    if execute_watch and save_state and output_dir and (expectations or expectation_files):
        if not expectation_errors and (expected_watches or expected_points):
            expectation_baseline = run_runtime_experiment(
                rom_path=rom_path or "pokegold.gbc", symbols_path=symbols_path, save_state=save_state,
                frames=frames, observe=tuple(expected_points), watch_symbols=tuple(expected_watches),
                interventions=(), root=root,
            )
            if expectation_baseline.get("executed") is not True:
                expectation_baseline.setdefault("errors", []).append("expectation baseline was not executed")
                expectation_baseline["valid"] = False
            if expectation_baseline.get("valid") and expectation_baseline.get("executed") is True and frames == 1:
                expectation_baseline["validation"] = {"minimal_positive_window": True}
                expectation_baseline.setdefault("known_limits", []).append(
                    "One frame is the minimum positive replay duration; the materialized state is not minimized."
                )
                path = str(output_dir / "04_expected_baseline.json").replace("'", "''")
                expectation_baseline["repro_command"] = f"python -m tools.audit.replay_runtime_experiment '{path}'"
            add_report(
                steps, produced_reports, report_paths, step_id="04_expected_baseline", phase="reproduce",
                title="Replay supplied behavior expectations", data=expectation_baseline, output_dir=output_dir, root=root,
            )

    captured_traces = []
    if execute_watch and save_state and output_dir:
        for index, capture in enumerate(localized_captures(
            localize, symbols=symbols, watch_symbols=tuple(unique_list([*expected_watches, *effective_watch_symbols])),
            rom_path=rom_path or "pokegold.gbc", symbols_path=symbols_path,
            save_state=save_state, frames=frames, max_targets=max_targets,
            max_events=max_events, output_dir=output_dir, root=root,
        ), 1):
            trace_output = capture.get("trace_output", {})
            if trace_output.get("written"):
                trace_path = resolve_path(trace_output.get("path", ""), root=root)
                if (capture.get("valid") is not True or capture.get("executed") is not True
                        or not capture.get("trace_sha256")
                        or sha256_file(trace_path) != capture["trace_sha256"]):
                    capture.setdefault("errors", []).append("captured trace is unexecuted, invalid, missing, or differs from its recorded hash")
                    capture["valid"] = False
            add_report(
                steps, produced_reports, report_paths,
                step_id=f"04_capture_{index}", phase="observe",
                title="Capture localized code" if index == 1 else "Expand observed code capture",
                data=capture, output_dir=output_dir, root=root,
            )
            if not capture.get("valid"):
                captured_traces.clear()
                break
            if trace_output.get("written"):
                captured_traces.append(trace_output["path"])
    effective_traces = (*traces, *captured_traces)
    if captured_traces:
        trace_index = build_trace_index_report(
            traces=effective_traces, symbols_path=symbols_path, max_events=max_events, root=root,
        )
        add_report(
            steps, produced_reports, report_paths, step_id="04_capture_index", phase="observe",
            title="Index captured execution", data=trace_index, output_dir=output_dir, root=root,
        )
        effects = build_effect_trace_report(
            traces=tuple(captured_traces), symbols_path=symbols_path, max_events=max_events,
            out_effects=display_output_path(output_dir / "capture_effects.jsonl", root=root), root=root,
        )
        proposals = {}
        hypothesis_observations = {}
        hypothesis_points = {}
        transport_traces = {}
        mbc3 = any(artifact.get("kind") == "rom" and artifact.get("sha256") == capture.get("rom_sha256")
                   and str(artifact.get("metadata", {}).get("cartridge_type", "")).lower() in
                   {"0x0f", "0x10", "0x11", "0x12", "0x13"} for artifact in ingest.get("artifacts", []))
        source_calls = {}
        mapped_sources = set()
        for event in effects.get("events", []):
            for atom in event.get("evidence_atoms", []):
                if atom.get("claim_type") == "diagnosis.hypothesis":
                    proposal = atom["detail"]["intervention"]
                    key = json.dumps(proposal, sort_keys=True)
                    proposals[key] = proposal
                    trace = event.get("trace_source", "")
                    if trace not in transport_traces:
                        loaded, trace_errors = load_traces(traces=(trace,), root=root) if trace else ([], ["missing trace"])
                        transport_traces[trace] = (trace_records(loaded[0]["data"]) if loaded else [], trace_errors)
                    records, trace_errors = transport_traces[trace]
                    input_change = atom["detail"].get("call_input_change")
                    if trace_errors:
                        transport = {"proof_status": "planned_only", "errors": trace_errors}
                    else:
                        transport = _register_transport(
                            records, register=proposal["register"],
                            start_seq=(input_change.get("entry_seq") if input_change else
                                       atom["detail"].get("call_register_change", {}).get("return_seq")),
                            end_seq=atom["detail"].get("consumer_seq"), mbc3=mbc3)
                    if input_change:
                        if "depends_on_return" in transport:
                            transport["depends_on_entry"] = transport.pop("depends_on_return")
                        for transfer in transport.get("transfers", []):
                            transfer["register_depends_on_entry"] = transfer.pop("register_depends_on_return")
                    atom["detail"]["register_transport"] = transport
                    hypothesis_observations.setdefault(key, []).append({
                        "trace": event.get("trace_source", ""), "seq": event.get("seq"),
                        "trace_sha256": sha256_file(event.get("trace_source", ""), root=root),
                        "consumer_seq": atom["detail"].get("consumer_seq"),
                        "comparison_seq": atom["detail"].get("comparison_seq"),
                        "call_register_change": atom["detail"].get("call_register_change", {}),
                        "register_transport": transport,
                    })
                    if "comparison_branch" in atom["detail"]:
                        hypothesis_observations[key][-1]["comparison_branch"] = atom["detail"]["comparison_branch"]
                    if input_change:
                        observation = hypothesis_observations[key][-1]
                        observation.pop("call_register_change")
                        observation.pop("comparison_seq")
                        observation["call_input_change"] = input_change
                        if "counted_pointer_loop" in atom["detail"]:
                            observation["counted_pointer_loop"] = atom["detail"]["counted_pointer_loop"]
                            observation.update(_loop_pointer_write(effects.get("events", []), records, observation, mbc3=mbc3))
                            observation.update(_loop_causal_chain(records, observation))
                    hypothesis_points.setdefault(key, []).extend(_hypothesis_observation_points(
                        effects.get("events", []), records, hypothesis_observations[key][-1], expected_watches))
                    for candidate in atom["detail"].get("source_candidates", []):
                        call = (candidate, event["bank"], event["pc"])
                        source_calls.setdefault(key, {})[json.dumps(call, sort_keys=True)] = call
        add_report(
            steps, produced_reports, report_paths, step_id="04_capture_effects", phase="observe",
            title="Attribute observed instruction effects", data=effects, output_dir=output_dir, root=root,
        )
        # These trials test source-derived hypotheses, not evaluator answers.
        # A changed output does not establish expected behavior or root cause.
        trial_watches = tuple(unique_list([*expected_watches, *[
            watch["name"] for watch in capture.get("watches", []) if watch.get("found")
        ]]))
        for index, proposal in enumerate(list(proposals.values())[:min(3, max_targets)], 1):
            required_points = unique_list([proposal["at"], *expected_points])
            extra_points = [point for point in unique_list(hypothesis_points.get(json.dumps(proposal, sort_keys=True), []))
                            if point not in required_points]
            trial_points = tuple([*required_points, *extra_points[:max(0, max_targets - len(required_points))]])
            transport_disproved = any(observation["register_transport"].get("depends_on_return") is False
                                      or observation["register_transport"].get("depends_on_entry") is False
                                      for observation in hypothesis_observations[json.dumps(proposal, sort_keys=True)])
            wrong_value = next((proposal["value"] + offset) & 255 for offset in (1, 2)
                               if ((proposal["value"] + offset) & 255) != proposal["expected"])
            control = {**proposal, "value": wrong_value}
            completed_trials = {}
            trial_checks = {}
            for mode, title, interventions in (
                ("baseline", "Replay hypothesis baseline", ()),
                ("restore", "Test register restoration", (proposal,)),
                ("control", "Test a different register value", (control,)),
            ):
                experiment = run_runtime_experiment(
                    rom_path=rom_path or "pokegold.gbc", symbols_path=symbols_path,
                    save_state=save_state, frames=frames, observe=trial_points,
                    watch_symbols=trial_watches, interventions=interventions, root=root,
                )
                for key in ("rom_sha256", "symbols_sha256", "state_basis", "backend", "backend_sha256"):
                    if not capture.get(key) or experiment.get(key) != capture[key]:
                        experiment.setdefault("errors", []).append(f"replay differs from captured {key}")
                        experiment["valid"] = False
                if experiment.get("executed") is not True:
                    experiment.setdefault("errors", []).append("hypothesis trial was not executed")
                    experiment["valid"] = False
                if experiment.get("valid") is True and experiment.get("executed") is True:
                    path = str(output_dir / f"04_trial_{index}_{mode}.json").replace("'", "''")
                    experiment["repro_command"] = f"python -m tools.audit.replay_runtime_experiment '{path}'"
                add_report(
                    steps, produced_reports, report_paths, step_id=f"04_trial_{index}_{mode}",
                    phase="compare", title=title,
                    data=experiment, output_dir=output_dir, root=root,
                )
                if not experiment.get("valid"):
                    break
                completed_trials[mode] = experiment
                if requested and not expectation_errors:
                    # Evaluate one trial at a time: restoration must never satisfy
                    # a baseline expectation through pooled evidence.
                    trial_contract = [dict(item) for item in requested]
                    if mode != "baseline":
                        for item in trial_contract:
                            operation = item.get("operation", "")
                            if operation.startswith("baseline."):
                                item["operation"] = "intervention." + operation.removeprefix("baseline.")
                    contract_path = output_dir / f"trial_{index}_{mode}_expectations.json"
                    write_json({"expectations": trial_contract}, contract_path)
                    trial_expect = build_expectation_report(
                        reports=(str(output_dir / f"04_trial_{index}_{mode}.json"),),
                        expectation_files=(str(contract_path),), symbols_path=symbols_path,
                        max_events=max_events, root=root,
                    )
                    add_report(steps, produced_reports, report_paths,
                               step_id=f"04_trial_{index}_{mode}_expect", phase="compare",
                               title=f"Check {mode} against supplied expectations", data=trial_expect,
                               output_dir=output_dir, root=root)
                    trial_checks[mode] = trial_expect
            if len(completed_trials) == 3:
                observed = {mode: trial.get("final", {}).get("watch_values", {}) for mode, trial in completed_trials.items()}
                # A wrong control can fail differently from the original bug.
                # Both must differ from restoration; the contract checks below
                # separately require baseline/control failure and restore success.
                if (not transport_disproved and all(observed.values())
                        and observed["restore"] != observed["baseline"]
                        and observed["restore"] != observed["control"]):
                    for key, (candidate, bank, pc) in source_calls.get(json.dumps(proposal, sort_keys=True), {}).items():
                        if key in mapped_sources or len(mapped_sources) >= max(0, min(3, max_targets, max_cases)):
                            continue
                        mapped_sources.add(key)
                        step_id = f"04_source_map_{len(mapped_sources)}"
                        build = source_mapping_builder(root, rom_path or "pokegold.gbc")
                        if build is None:
                            add_skipped_step(steps, step_id=step_id, phase="localize", title="Verify source call address",
                                             reason="a prepared Makefile and configured RGBDS build tree are required")
                            continue
                        try:
                            mapping = build_source_mapping_report(
                                root=root, destination=Path(tempfile.gettempdir()) / f"debugger-source-{uuid.uuid4().hex}",
                                candidate=candidate, bank=bank, pc=pc, build=build,
                                rom_path=str(resolve_path(rom_path or "pokegold.gbc", root=root).relative_to(root.resolve())),
                                symbols_path=str(resolve_path(symbols_path, root=root).relative_to(root.resolve())),
                            )
                            for identity_key in ("rom_sha256", "symbols_sha256"):
                                if not capture.get(identity_key) or mapping.get(identity_key) != capture[identity_key]:
                                    mapping.setdefault("errors", []).append(f"source mapping differs from captured {identity_key}")
                                    mapping["valid"] = False
                                    mapping["evidence_atoms"] = []
                            mapping["error_count"] = len(mapping.get("errors", []))
                        except (ValueError, OSError) as exc:
                            mapping = {"kind": "unified_debugger_provenance_report", "valid": False, "errors": [str(exc)]}
                        add_report(steps, produced_reports, report_paths, step_id=step_id, phase="localize",
                                   title="Verify source call address", data=mapping, output_dir=output_dir, root=root)
                        if (mapping.get("valid") and len(trial_checks) == 3
                                and all(check.get("valid") is True and check.get("expectation_count", 0) > 0
                                        for check in trial_checks.values())
                                and trial_checks["baseline"].get("passed") is False
                                and trial_checks["restore"].get("passed") is True
                                and trial_checks["control"].get("passed") is False):
                            for mapped in mapping.get("evidence_atoms", []):
                                if (mapped.get("claim_type") != "provenance.source_mapping"
                                        or mapped.get("proof_status") != "mirror_passed"):
                                    continue
                                investigation_evidence.append(evidence_atom(
                                    claim_type="diagnosis.hypothesis", origin="investigate",
                                    observation_type="controlled_runtime_comparison", proof_status="instruction_observed",
                                    source_report=str(output_dir / f"{step_id}.json"), source_kind=mapping["kind"],
                                    precision=mapped["precision"],
                                    scope={key: capture[key] for key in
                                           ("rom_sha256", "symbols_sha256", "state_basis", "backend", "backend_sha256")},
                                    detail={
                                        "intervention": proposal,
                                        "observations": hypothesis_observations[json.dumps(proposal, sort_keys=True)],
                                        "expectations": requested,
                                        "reproducer": str(output_dir / f"04_trial_{index}_baseline.json"),
                                        "regression": str(output_dir / f"trial_{index}_baseline_expectations.json"),
                                        "checkpoint_comparison": _trial_checkpoint_comparison(completed_trials),
                                        "trials": {mode: {
                                            "report": str(output_dir / f"04_trial_{index}_{mode}.json"),
                                            "report_sha256": sha256_file(output_dir / f"04_trial_{index}_{mode}.json"),
                                            "expectation_report": str(output_dir / f"04_trial_{index}_{mode}_expect.json"),
                                            "expectation_report_sha256": sha256_file(output_dir / f"04_trial_{index}_{mode}_expect.json"),
                                        } for mode in completed_trials},
                                        "source_sha256": mapped.get("detail", {}).get("source_sha256", ""),
                                        "source_mapping_sha256": sha256_file(output_dir / f"{step_id}.json"),
                                        "uncertainty": "Source-mapped intervention satisfies the supplied contract and the control does not; the complete initiating-cause dependency chain, independent intent, and corrected-source regression remain unverified. The regression file contains only the supplied expectations.",
                                    },
                                ))
            if frames > 1 and len(completed_trials) == 3 and all(
                trial.get("events") and trial.get("final", {}).get("watch_values")
                for trial in completed_trials.values()
            ):
                short_trials = []
                for mode, reference in completed_trials.items():
                    interventions = tuple({key: patch[key] for key in ("at", "register", "expected", "value")}
                                          for patch in reference["interventions"])
                    short = run_runtime_experiment(
                        rom_path=rom_path or "pokegold.gbc", symbols_path=symbols_path, save_state=save_state,
                        frames=1, observe=trial_points, watch_symbols=trial_watches,
                        interventions=interventions, root=root,
                    )
                    if short.get("executed") is not True:
                        short.setdefault("errors", []).append("one-frame replay was not executed")
                        short["valid"] = False
                    expected_basis = {**reference["state_basis"], "inputs": {"frames": 1, "events": []},
                                      "input_log_sha256": replay_state_basis(None, 1)["input_log_sha256"]}
                    identity_matches = short.get("state_basis") == expected_basis and all(
                        short.get(key) == reference.get(key)
                        for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256")
                    )
                    if not identity_matches:
                        short.setdefault("errors", []).append("one-frame replay identity differs from reference")
                        short["valid"] = False
                    preserved = bool(short.get("valid") and identity_matches
                                     and short.get("initial") == reference.get("initial")
                                     and short.get("events") == reference.get("events")
                                     and short.get("final", {}).get("watch_values") == reference["final"]["watch_values"])
                    short["validation"] = {"preserved_reference_observations": preserved}
                    short_trials.append((mode, short))
                    if not preserved:
                        break
                minimized = len(short_trials) == 3 and all(
                    trial["validation"]["preserved_reference_observations"] for _, trial in short_trials
                )
                for mode, short in short_trials:
                    step_id = f"04_short_{index}_{mode}"
                    short["validation"]["minimal_positive_window"] = minimized
                    short.setdefault("known_limits", []).append(
                        "This checks observed checkpoint events and final watches; materialized state and gameplay reachability are not minimized."
                    )
                    path = str(output_dir / f"{step_id}.json").replace("'", "''")
                    if short.get("valid"):
                        short["repro_command"] = f"python -m tools.audit.replay_runtime_experiment '{path}'"
                    add_report(
                        steps, produced_reports, report_paths, step_id=step_id, phase="minimize",
                        title=f"Check one-frame {mode} replay", data=short, output_dir=output_dir, root=root,
                    )

    coverage = build_coverage_report(
        traces=effective_traces,
        reports=tuple(report_paths),
        symbols=tuple(unique_list([*symbols, *effective_watch_symbols])),
        rules=rules,
        changed_files=changed_files,
        symbols_path=symbols_path,
        max_targets=max_targets * 2,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="05_coverage",
        phase="coverage",
        title="Measure evidence coverage",
        data=coverage,
        output_dir=output_dir,
        root=root,
    )

    explain = build_explanation_report(
        reports=tuple(report_paths),
        traces=effective_traces,
        symbols=symbols,
        watch_symbols=effective_watch_symbols,
        changed_files=changed_files,
        symptom=symptom,
        symbols_path=symbols_path,
        depth=2,
        max_paths=max_targets,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="06_explain",
        phase="explain",
        title="Explain causal paths",
        data=explain,
        output_dir=output_dir,
        root=root,
    )

    taint_symbols = tuple(
        unique_list(
            [
                *effective_watch_symbols,
                *state_symbols_from_trace_index(trace_index),
                *state_like_symbols(symbols),
            ]
        )[:max_targets]
    )
    if taint_symbols:
        taint_source_files = tuple(
            path
            for path in changed_files
            if Path(path).suffix.lower() == ".asm"
        )
        taint = build_taint_report(
            symbols_path=symbols_path,
            symbols=taint_symbols,
            source_files=taint_source_files,
            max_depth=80,
            max_paths=max_targets,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="06_taint",
            phase="explain",
            title="Build source-level taint paths",
            data=taint,
            output_dir=output_dir,
            root=root,
        )
    else:
        add_skipped_step(
            steps,
            step_id="06_taint",
            phase="explain",
            title="Build source-level taint paths",
            reason="no --symbol or --watch-symbol inputs were supplied",
        )

    compare = build_compare_plan(
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="07_compare",
        phase="compare",
        title="Route mirrors and expectations",
        data=compare,
        output_dir=output_dir,
        root=root,
    )

    if content_files:
        content_mirror = build_content_mirror_report(
            changed_files=content_files,
            max_files=max_targets,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="07_content_mirror",
            phase="compare",
            title="Check content source mirrors",
            data=content_mirror,
            output_dir=output_dir,
            root=root,
        )

    if expectations or expectation_files:
        expect = build_expectation_report(
            reports=tuple(report_paths),
            traces=effective_traces,
            expectation_files=expectation_files,
            expectations=expectations,
            symptom=symptom,
            symbols_path=symbols_path,
            max_events=max_events,
            root=root,
        )
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="08_expect",
            phase="compare",
            title="Evaluate behavior expectations",
            data=expect,
            output_dir=output_dir,
            root=root,
        )
    else:
        add_skipped_step(
            steps,
            step_id="08_expect",
            phase="compare",
            title="Evaluate behavior expectations",
            reason="no --expect or --expect-file inputs were supplied",
        )

    seed_manifest = display_output_path(output_dir / "generated_seeds.jsonl", root=root) if output_dir else ""
    generate = build_generation_plan(
        reports=tuple(report_paths),
        scenarios=scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        out_scenarios=seed_manifest,
        max_cases=max_cases,
        seed=seed,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="09_generate",
        phase="generate",
        title="Plan counterexample generation",
        data=generate,
        output_dir=output_dir,
        root=root,
    )

    fuzz = build_fuzz_plan(
        reports=tuple(report_paths),
        scenarios=scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        out_cases=display_output_path(output_dir / "fuzz_cases.jsonl", root=root) if output_dir else "",
        max_cases=max_cases,
        seed=seed,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="09_fuzz",
        phase="generate",
        title="Plan fuzz campaigns",
        data=fuzz,
        output_dir=output_dir,
        root=root,
    )

    if expectation_baseline and expectation_baseline.get("valid"):
        # Preserve observations, including failures, independently of the desired
        # behavior. Ascending trials establish a minimum without assuming monotonicity.
        minimize = dict(expectation_baseline)
        attempts = []
        minimum_found = frames == 1
        for duration in range(1, min(frames, max(0, max_cases) + 1)):
            candidate = run_runtime_experiment(
                rom_path=rom_path or "pokegold.gbc", symbols_path=symbols_path, save_state=save_state,
                frames=duration, observe=tuple(expected_points), watch_symbols=tuple(expected_watches),
                interventions=(), root=root,
            )
            if candidate.get("executed") is not True:
                candidate.setdefault("errors", []).append("duration candidate was not executed")
                candidate["valid"] = False
            expected_basis = {**expectation_baseline["state_basis"], "inputs": {"frames": duration, "events": []},
                              "input_log_sha256": replay_state_basis(None, duration)["input_log_sha256"]}
            same_identity = candidate.get("state_basis") == expected_basis and all(
                expectation_baseline.get(key) and candidate.get(key) == expectation_baseline[key]
                for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256")
            )
            preserved = bool(same_identity and candidate.get("valid")
                             and candidate.get("initial") == expectation_baseline.get("initial")
                             and candidate.get("events") == expectation_baseline.get("events")
                             and candidate.get("final", {}).get("watch_values") == expectation_baseline.get("final", {}).get("watch_values"))
            candidate["validation"] = {"preserved_reference_observations": preserved}
            candidate_path = output_dir / f"10_candidate_{duration}.json"
            write_json(candidate, candidate_path)
            attempts.append({"report": str(candidate_path), "frames": duration, "preserved": preserved})
            if not same_identity:
                minimize["valid"] = False
                minimize["errors"] = [*minimize.get("errors", []), "duration candidate identity differs from baseline"]
                break
            if preserved:
                minimize = candidate
                minimum_found = True
                break
            if not candidate.get("valid") and not (
                candidate.get("executed") is True and candidate.get("errors")
                and all(error.startswith("checkpoint not reached:") for error in candidate["errors"])
            ):
                break
            minimum_found = duration == frames - 1
        minimize["validation"] = {**minimize.get("validation", {}), "minimal_positive_window": minimum_found,
                                  "reference_report": str(output_dir / "04_expected_baseline.json"), "attempts": attempts}
        minimize["known_limits"] = [*minimize.get("known_limits", []),
                                   "Duration trials preserve initial/checkpoint observations and final watches, not all materialized RAM or gameplay reachability."]
        if not minimum_found:
            minimize["known_limits"].append("The bounded duration search did not establish a minimum; the original baseline is retained.")
        path = str(output_dir / "10_minimize.json").replace("'", "''")
        if minimize.get("valid"):
            minimize["repro_command"] = f"python -m tools.audit.replay_runtime_experiment '{path}'"
        else:
            minimize.pop("repro_command", None)
    else:
        minimize = build_minimization_plan(
            reports=tuple(report_paths),
            traces=effective_traces,
            scenarios=scenarios,
            symbols=symbols,
            rules=rules,
            addresses=addresses,
            expectations=expectations,
            expectation_files=expectation_files,
            changed_files=changed_files,
            symptom=symptom,
            out_trace=display_output_path(output_dir / "minimized_trace.json", root=root) if output_dir else "",
            symbols_path=symbols_path,
            max_scenarios=min(max_cases, 20),
            root=root,
        )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="10_minimize",
        phase="minimize",
        title="Reduce baseline replay duration" if expectation_baseline and expectation_baseline.get("valid") else "Plan minimization",
        data=minimize,
        output_dir=output_dir,
        root=root,
    )

    rank = rank_findings(reports=tuple(report_paths), root=root)
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="11_rank",
        phase="rank",
        title="Rank findings",
        data=rank,
        output_dir=output_dir,
        root=root,
    )

    impact = build_impact_report(
        reports=tuple(report_paths),
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        max_items=max_targets * 2,
        root=root,
    )
    add_report(
        steps,
        produced_reports,
        report_paths,
        step_id="12_impact",
        phase="rank",
        title="Rank impact",
        data=impact,
        output_dir=output_dir,
        root=root,
    )

    static_report_path = ""
    visualization_path = ""
    static_report_json = None
    visualization_json = None
    if output_dir:
        static_report_json = build_static_report(
            reports=tuple(report_paths),
            output_format="markdown",
            title="Unified Pokemon Gold Romhack Debugger Investigation",
            root=root,
        )
        static_report_json["content"] = _with_hypothesis_overview(
            static_report_json["content"], [(atom, root) for atom in investigation_evidence], "markdown")
        static_report_file = output_dir / "investigation_report.md"
        write_static_report(static_report_json, static_report_file)
        static_report_path = display_output_path(static_report_file, root=root)
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="13_report",
            phase="report",
            title="Render static report",
            data=static_report_json,
            output_dir=output_dir,
            root=root,
        )

        visualization_json = build_visualization_report(
            reports=tuple(report_paths),
            traces=traces,
            output_format="markdown",
            title="Unified Pokemon Gold Romhack Debugger Investigation",
            max_items=max(80, max_targets * 4),
            root=root,
        )
        visualization_file = output_dir / "investigation_visualization.md"
        write_visualization(visualization_json, visualization_file)
        visualization_path = display_output_path(visualization_file, root=root)
        add_report(
            steps,
            produced_reports,
            report_paths,
            step_id="14_visualize",
            phase="report",
            title="Render visualization",
            data=visualization_json,
            output_dir=output_dir,
            root=root,
        )

    errors = unique_list(
        error
        for step in steps
        for error in step.get("errors", [])
    )
    if source_basis:
        try:
            if source_manifest_hash(root) != source_basis:
                raise ValueError("source manifest changed during investigation")
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
            source_basis = ""
    warnings = unique_list(
        warning
        for step in steps
        for warning in step.get("warnings", [])
    )
    commands = unique_list(
        command
        for step in steps
        for command in step.get("commands", [])
    )
    failed_expectations = expectation_failures(produced_reports)
    failed_steps = [step for step in steps if step.get("status") == "failed"]
    skipped_steps = [step for step in steps if step.get("status") == "skipped"]

    result = {
        "schema_version": 1,
        "kind": "unified_debugger_investigation_run",
        "root": str(root),
        "valid": not errors,
        "passed": not errors and not failed_expectations and not failed_steps,
        "out_dir": display_output_path(output_dir, root=root) if output_dir else "",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "input_reports": list(reports),
        "input_traces": list(traces),
        "patches": list(patches),
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "watch_symbols": list(watch_symbols),
        "effective_watch_symbols": list(effective_watch_symbols),
        "rules": list(rules),
        "addresses": list(addresses),
        "symptom": symptom,
        "phase_count": len({step["phase"] for step in steps}),
        "investigation_step_count": len(steps),
        "produced_report_count": len(produced_reports),
        "failed_count": len(failed_steps) + len(failed_expectations),
        "skipped_count": len(skipped_steps),
        "steps": steps,
        "reports": produced_reports,
        "evidence_atoms": investigation_evidence,
        "report_paths": report_paths,
        "finding_count": int(rank.get("finding_count", 0)),
        "impact_count": int(impact.get("impact_count", 0)),
        "top_findings": rank.get("findings", [])[:20],
        "top_impact": impact.get("items", [])[:20],
        "static_report": static_report_path,
        "visualization": visualization_path,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This command coordinates the investigation packet; expensive subsystem commands are planned unless their underlying tool explicitly executes inside a report.",
            "A complete investigation packet is only proof when the included evidence is ROM-backed and any expectation report passed.",
            "Subsystem semantic reducers and exact mirrors still own behavior-specific proof where they exist.",
        ],
    }
    if source_basis:
        result["source_tree_sha256"] = source_basis
    if symptom_only_next_step is not None:
        result["symptom_only_next_step_note"] = symptom_only_next_step_note
        result["symptom_only_next_step"] = symptom_only_next_step
    return result


def _trial_checkpoint_comparison(trials):
    """Compare visits to captured PCs, retaining references to every occurrence."""
    comparison = {"checkpoints": [], "errors": [],
        "scope": "Visits are grouped by bank and PC and listed in observation order, not assumed to be equivalent loop iterations. after_registers is after any intervention, before instruction execution, and is omitted when it repeats the pre-intervention values. Constant values are not differences merely because hit counts differ. Differences are observations, not a complete causal proof."}
    grouped = {}
    for mode, trial in trials.items():
        events = trial.get("events", [])
        sequences = [event.get("seq") for event in events]
        if any(type(seq) is not int or seq < 0 for seq in sequences) or sequences != sorted(set(sequences)):
            comparison["errors"].append(f"{mode} checkpoint sequences are missing, duplicated, or out of order")
            continue
        for event in events:
            key = (event["bank"], event["pc"])
            grouped.setdefault(key, {}).setdefault(mode, []).append(event)
    if comparison["errors"]:
        return comparison
    for (bank, pc), visits in grouped.items():
        rows = {mode: visits.get(mode, []) for mode in trials}
        differences = {}
        for field in ("registers", "after_registers", "watch_values"):
            names = sorted({name for events in rows.values() for event in events for name in event.get(field, {})})
            for name in names:
                if field == "after_registers" and all(event.get(field, {}).get(name) == event.get("registers", {}).get(name)
                                                     for events in rows.values() for event in events):
                    continue
                values = {mode: [event.get(field, {}).get(name) for event in events] for mode, events in rows.items()}
                if all(values.values()) and all(value == values["baseline"][0] for visits in values.values() for value in visits):
                    continue  # Different hit counts alone do not change a constant value.
                if any(values[mode] != values["baseline"] for mode in values):
                    differences.setdefault(field, {})[name] = {
                        mode: [{"seq": event["seq"], **({"value": event[field][name]} if name in event.get(field, {}) else {})}
                               for event in events] for mode, events in rows.items()}
        comparison["checkpoints"].append({
            "bank": bank, "pc": pc,
            "targets": unique_list([target for events in rows.values() for event in events for target in event.get("targets", [])]),
            "seqs": {mode: [event["seq"] for event in events] for mode, events in rows.items()},
            "hit_counts": {mode: len(events) for mode, events in rows.items()},
            "differences": differences,
        })
    return comparison


def _loop_pointer_write(events, records, observation, *, mbc3):
    """Connect a counted-loop base to an HL-based store with identified MBC3 state.

    A preceding ROMX frame supplies bank context across calls into ROM0. The
    dependency checker validates the complete interval rather than guessing the
    selected bank at the loop's ROM0 return instruction.
    """
    if not mbc3:
        return {}
    loop = observation["counted_pointer_loop"]
    def pointer(event):
        if not {"H", "L"} <= set(event.get("known_registers", [])):
            return None
        return int(event["pre_registers"]["H"] + event["pre_registers"]["L"], 16)

    window = [event for event in events if event.get("trace_source") == observation["trace"]]
    contexts = [event for event in window if event["seq"] < loop["input_seq"]
                and 0x4000 <= event.get("pc", 0) < 0x8000 and event.get("bank", 0) > 0
                and pointer(event) == loop["pointer_initial"]]
    if not contexts:
        return {}
    context = max(contexts, key=lambda event: event["seq"])
    stores = [(event, effect) for event in window if event["seq"] >= loop["exit_seq"]
              and event.get("opcode") in {0x22, 0x32, 0x36, *range(0x70, 0x76), 0x77}
              and pointer(event) == loop["pointer_final"]
              for effect in event.get("effects", []) if effect.get("access") == "write"
              and effect.get("space") == "sram" and type(effect.get("bank")) is int and 0 <= effect["bank"] <= 3
              and effect.get("sram_enabled") == 1 and effect.get("address") == loop["pointer_final"]]
    if not stores:
        return {}
    event, store = min(stores, key=lambda item: item[0]["seq"])
    registers = {}
    for register in ("H", "L"):
        transport = _register_transport(records, register=register, start_seq=context["seq"], end_seq=event["seq"], mbc3=True)
        if "depends_on_return" in transport:
            transport["depends_on_pointer_base"] = transport.pop("depends_on_return")
        for transfer in transport.get("transfers", []):
            transfer["depends_on_pointer_base"] = transfer.pop("register_depends_on_return")
        registers[register] = transport
    return {"pointer_write": {
        "context_seq": context["seq"], "registers": registers,
        "store": {"seq": event["seq"], "pc": event["pc"], "instruction_bank": event["bank"],
                  **{key: store[key] for key in ("address", "bank", "value", "bank_source", "sram_enabled", "sram_enabled_source") if key in store}},
        "scope": "Pointer-base byte dependencies and modeled MBC3 store context; memory contents and intended ownership require independent checks.",
    }}


def _loop_causal_chain(records, observation):
    """Cite an observed farcall/loop/fill path without promoting its hypothesis.

    Existing dependency checks supply the loop and pointer link. These anchors
    make the evidence replayable; they do not supply intent or corrected source.
    """
    loop = observation["counted_pointer_loop"]
    pointer = observation.get("pointer_write", {})
    if (observation["register_transport"].get("depends_on_entry") is not True
            or observation["register_transport"].get("proof_status") != "taint_proven"
            or loop.get("proof_status") != "instruction_observed"
            or any(pointer.get("registers", {}).get(register, {}).get("depends_on_pointer_base") is not True
                   or pointer.get("registers", {}).get(register, {}).get("proof_status") != "taint_proven"
                   for register in ("H", "L"))):
        return {}
    by_seq = {record.get("seq"): record for record in records}
    start = observation["seq"]
    setup, address, restart = (by_seq.get(start + offset, {}) for offset in range(3))
    if [record.get("opcode") for record in (setup, address, restart)] != [0x3E, 0x21, 0xCF]:
        return {}
    store_seq = pointer.get("store", {}).get("seq")
    if type(store_seq) is not int:
        return {}
    returns = [record for record in records if type(record.get("seq")) is int and record["seq"] > store_seq
               and record.get("pc") == restart.get("pc", -1) + 1 and record.get("bank") == restart.get("bank")
               and type(record.get("regs", {}).get("SP")) is int
               and record["regs"]["SP"] == restart.get("regs", {}).get("SP")]
    if not returns:
        return {}
    end = returns[0]["seq"]
    window = [record for record in records if type(record.get("seq")) is int and start <= record["seq"] <= end]
    if [record["seq"] for record in window] != list(range(start, end + 1)):
        return {}
    fills = []
    for record in window:
        if not loop["exit_seq"] <= record["seq"] < store_seq or record.get("opcode") != 0xCD:
            continue
        operand = record.get("operand", [])
        if len(operand) != 2:
            continue
        target = operand[0] + 256 * operand[1]
        entry = by_seq.get(record["seq"] + 1, {})
        if (0 <= target < 0x8000 and entry.get("pc") == target
                and entry.get("bank") == (0 if target < 0x4000 else record.get("bank"))
                and type(entry.get("regs", {}).get("SP")) is int
                and entry["regs"]["SP"] == by_seq[store_seq].get("regs", {}).get("SP")):
            fills.append(entry["seq"])
    iterations = loop.get("iteration_seqs", [])
    if not fills or len(iterations) != loop.get("iterations") or not all(iterations):
        return {}
    anchors = [start, start + 1, observation["call_input_change"]["entry_seq"], loop["input_seq"],
               *[iteration[0] for iteration in iterations], fills[-1], end]
    if any(type(seq) is not int or seq not in by_seq for seq in anchors) or anchors != sorted(set(anchors)):
        return {}
    return {"causal_chain": [{"trace": observation["trace"], "trace_sha256": observation["trace_sha256"], "seq": seq}
                             for seq in anchors]}


def _hypothesis_observation_points(events, records, observation, watches):
    """Choose replay checkpoints; selection alone does not prove a dependency."""
    branch = observation.get("comparison_branch")
    input_change = observation.get("call_input_change")
    if input_change:
        start_seq = observation["consumer_seq"]
        change_start_seq = start_seq
    elif branch:
        start_seq = observation["comparison_seq"]
        change_start_seq = branch["successor_seq"]
    else:
        return []
    end_seq = None
    for before, after in zip(records, records[1:]):
        if type(before.get("seq")) is not int or before["seq"] < change_start_seq:
            continue
        old, new = before.get("watch_values", {}), after.get("watch_values", {})
        if any(watch in old and watch in new and old[watch] != new[watch] for watch in watches):
            end_seq = before["seq"]
            break
    if end_seq is None:
        return []
    window = [event for event in events if event.get("trace_source") == observation["trace"]
              and start_seq <= event["seq"] <= end_seq]
    by_seq = {event["seq"]: event for event in window}
    if input_change:
        priority = [start_seq, *[event["seq"] for event in window
                                if event.get("opcode") in {*CONDITIONAL_JUMPS, *CONDITIONAL_RETS}], end_seq]
    else:
        priority = [start_seq, branch["branch_seq"], branch["successor_seq"], end_seq]
    # Repeated arithmetic PCs are sampled on every hit by the runtime, exposing
    # loop counts as well as the value handed to the final observed store.
    arithmetic = [event["seq"] for event in window if any(
        effect.get("access") == "register_write" and "updates" not in effect.get("operation", "")
        and any(source.get("kind") == "register" and source.get("name", "").upper() == effect.get("register")
                for source in effect.get("source_operands", []))
        for effect in event.get("effects", []))]
    return unique_list([by_seq[seq]["pc_label"] for seq in [*priority, *arithmetic]
                        if seq in by_seq and by_seq[seq].get("pc_label")])


def source_mapping_builder(root: Path, rom_path: str):
    """Use only the prepared tree's declared RGBDS toolchain and fixed build recipe."""
    version_file = root / ".rgbds-version"
    if not (root / "Makefile").is_file() or not version_file.is_file():
        return None
    version = version_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        return None
    suffix = ".exe" if os.name == "nt" else ""
    names = ("rgbasm", "rgblink", "rgbfix", "rgbgfx")
    directory = f"rgbds-{version}"
    if not all((root / directory / (name + suffix)).is_file() for name in names):
        return None
    if not shutil.which("bash" if os.name == "nt" else "make"):
        return None
    command = ["make", "-j4", "PYTHON=python3", *[f"{name.upper()}={directory}/{name}{suffix}" for name in names],
               "branch_currency_banner=", rom_path]
    if os.name == "nt":
        command = ["bash", "-lc", shlex.join(command)]
    return lambda destination: subprocess.run(command, cwd=destination, capture_output=True, text=True, timeout=120)


def localized_captures(
    localize, *, symbols, watch_symbols, rom_path, symbols_path, save_state,
    frames, max_targets, max_events, output_dir, root,
):
    """Capture candidates, then widen code reachable from observed hits.

    Three fresh-state trials bound the work. Missing hits do not disprove a
    candidate outside the window, and an observed call is not causal proof.
    Never repeat an identical target set or edit the source/state to get a hit.
    """
    sym = resolve_path(symbols_path, root=root)
    table = parse_symbol_table(sym) if sym.is_file() else {}
    graph = build_static_call_graph(root=root)
    code_labels = {block.label for block in graph.blocks.values()
                   if any(line.code.split()[0].lower() in LINE_OPS - DATA_OPS for line in block.lines)}
    code_labels.update(block.parent_label for block in graph.blocks.values() if block.label in code_labels)
    retrieved = [item["symbol"] for item in localize.get("signals", [])
                 if item.get("type") == "source_retrieval"]
    selected = [name for name in unique_list([
        *symbols, *(retrieved or [item["id"] for item in localize.get("candidates", [])
                                 if item.get("type") == "symbol"]),
    ]) if name in code_labels and is_traceable_function(name, table)][:max_targets]
    if not selected:
        return
    attempted = set()
    for trial in range(1, 4):
        key = frozenset(selected)
        if not key or key in attempted:
            break
        attempted.add(key)
        watch_groups = []
        for name in selected:
            blocks = [block for block in graph.blocks.values()
                      if block.label == name or block.parent_label == name]
            watch_groups.append(unique_list(
                token for block in blocks for line in block.lines
                for token in TOKEN_RE.findall(line.code) if is_watch_symbol(token, table)
            ))
        # Round-robin avoids one large candidate consuming the entire watch
        # budget before later candidates contribute any relevant state.
        inferred = unique_list(token for row in zip_longest(*watch_groups) for token in row if token)
        watches = tuple(unique_list([*watch_symbols, *inferred])[:max_targets])
        capture = build_instruction_trace_report(
            function_symbols=tuple(selected), watch_symbols=watches, rom_path=rom_path,
            symbols_path=symbols_path, save_state=save_state, frames=frames,
            max_functions=max_targets, max_frames=max_events, execute=True, require_hit=True,
            out_trace=display_output_path(output_dir / f"capture_{trial}.jsonl", root=root), root=root,
        )
        yield capture
        if not capture.get("valid"):
            break
        hits = capture.get("execution_validation", {}).get("hit_function_symbols", [])
        if not hits:
            break
        parents = {graph.blocks[name].parent_label for name in hits if name in graph.blocks}
        related = [block.label for block in graph.blocks.values() if block.parent_label in parents]
        expanded_callers = {*hits, *related}
        callees = [edge.callee for edge in graph.edges
                   if edge.caller in expanded_callers and edge.callee]
        dispatch = []
        trace_output = capture.get("trace_output", {})
        if capture.get("executed") and trace_output.get("written"):
            trace_path = resolve_path(trace_output["path"], root=root)
            if capture.get("trace_sha256") and sha256_file(trace_path) == capture["trace_sha256"]:
                loaded, errors = load_traces(traces=(str(trace_path),), root=root)
                if not errors:
                    vectors = {record["opcode"] & 0x38 for item in loaded for record in trace_records(item["data"])
                               if type(record.get("opcode")) is int and 0 <= record["opcode"] <= 255
                               and record["opcode"] & 0xC7 == 0xC7}
                    dispatch = [name for name, entry in table.items() if entry["bank"] == 0
                                and entry["address"] in vectors and name in code_labels][:max_targets]
        # RST vectors often jump through a small bank-switch dispatcher. Include
        # its source-reachable helpers in this pass, still within the same budget.
        for name in dispatch:
            for edge in graph.edges:
                if (len(dispatch) < max_targets and edge.caller == name and edge.callee in code_labels
                        and edge.callee not in dispatch):
                    dispatch.append(edge.callee)
        selected = [name for name in unique_list([*hits, *dispatch, *callees, *related])
                    if is_traceable_function(name, table)][:max_targets]


def investigation_has_anchor(
    *,
    rom_path: str,
    save_state: str,
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    reports: tuple[str, ...],
    patches: tuple[str, ...],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    rules: tuple[str, ...],
    addresses: tuple[str, ...],
    expectations: tuple[str, ...],
    expectation_files: tuple[str, ...],
    families: tuple[str, ...],
) -> bool:
    return any(
        (
            rom_path,
            save_state,
            traces,
            scenarios,
            reports,
            patches,
            changed_files,
            symbols,
            watch_symbols,
            rules,
            addresses,
            expectations,
            expectation_files,
            families,
        )
    )


def add_report(
    steps: list[dict[str, Any]],
    produced_reports: list[dict[str, Any]],
    report_paths: list[str],
    *,
    step_id: str,
    phase: str,
    title: str,
    data: dict[str, Any],
    output_dir: Path | None,
    root: Path,
) -> None:
    path = ""
    if output_dir:
        path_obj = output_dir / f"{step_id}.json"
        write_json(data, path_obj)
        path = display_output_path(path_obj, root=root)
        report_paths.append(path)
    report_ref = {
        "id": step_id,
        "kind": str(data.get("kind", "")),
        "path": path,
        "valid": bool(data.get("valid", True)),
        "passed": data.get("passed"),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
    }
    produced_reports.append(report_ref)
    status = "completed" if report_ref["valid"] else "failed"
    steps.append(
        {
            "id": step_id,
            "phase": phase,
            "title": title,
            "status": status,
            "report_kind": report_ref["kind"],
            "report_path": path,
            "valid": report_ref["valid"],
            "summary": summarize_report(data),
            "errors": list(data.get("errors", []))[:8],
            "warnings": list(data.get("warnings", []))[:8],
            "commands": collect_report_commands(data)[:24],
        }
    )


def add_skipped_step(
    steps: list[dict[str, Any]],
    *,
    step_id: str,
    phase: str,
    title: str,
    reason: str,
) -> None:
    steps.append(
        {
            "id": step_id,
            "phase": phase,
            "title": title,
            "status": "skipped",
            "report_kind": "",
            "report_path": "",
            "valid": True,
            "summary": {"reason": reason},
            "errors": [],
            "warnings": [reason],
            "commands": [],
        }
    )


def state_symbols_from_trace_index(report: dict[str, Any]) -> list[str]:
    symbols = []
    for event in dict_items(report.get("events")):
        symbol = str(event.get("state_symbol", ""))
        if is_state_symbol(symbol):
            symbols.append(symbol)
    for attribution in dict_items(report.get("reverse_attributions")):
        symbol = str(attribution.get("state", ""))
        if is_state_symbol(symbol):
            symbols.append(symbol)
        for related in string_items(attribution.get("related_symbols")):
            if is_state_symbol(related):
                symbols.append(related)
    return unique_list(symbols)


def state_like_symbols(symbols: tuple[str, ...]) -> list[str]:
    return [symbol for symbol in symbols if is_state_symbol(symbol)]


def is_state_symbol(symbol: str) -> bool:
    return str(symbol).startswith(("w", "h", "s", "v", "r"))


def summarize_report(data: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "valid",
        "passed",
        "artifact_count",
        "event_count",
        "dynamic_context_event_count",
        "matched_event_count",
        "reverse_attribution_count",
        "write_attribution_count",
        "invariant_count",
        "failed_invariant_count",
        "rom_mirror_count",
        "failed_rom_mirror_count",
        "path_count",
        "candidate_count",
        "target_count",
        "uncovered_target_count",
        "match_count",
        "expectation_count",
        "failed_count",
        "scenario_count",
        "behavioral_probe_count",
        "generator_count",
        "finding_count",
        "impact_count",
        "investigation_step_count",
        "produced_report_count",
        "command_count",
        "timeline_event_count",
        "graph_node_count",
    )
    return {key: data[key] for key in keys if key in data}


def collect_report_commands(data: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    add_strings(commands, data.get("repro_command"))
    recommendation = data.get("recommendation") if isinstance(data.get("recommendation"), dict) else {}
    add_strings(commands, recommendation.get("first_command"))
    add_strings(commands, recommendation.get("regression_gate"))
    add_strings(commands, recommendation.get("escalation_command"))
    add_strings(commands, data.get("commands"))
    add_strings(commands, data.get("runnable_commands"))
    add_strings(commands, data.get("blocked_commands"))
    add_strings(commands, data.get("materialization_commands"))
    for phase in dict_items(data.get("phase_steps")):
        for step in dict_items(phase.get("steps")):
            add_strings(commands, step.get("command"))
    for step in dict_items(data.get("steps")):
        add_strings(commands, step.get("command"))
        add_strings(commands, step.get("commands"))
    for item in dict_items(data.get("items")):
        add_strings(commands, item.get("next_actions"))
    for finding in dict_items(data.get("findings")):
        add_strings(commands, finding.get("next_actions"))
    for attribution in dict_items(data.get("reverse_attributions")):
        add_strings(commands, attribution.get("commands"))
    for attribution in dict_items(data.get("write_attributions")):
        add_strings(commands, attribution.get("commands"))
    for expectation in dict_items(data.get("expectations")):
        add_strings(commands, expectation.get("commands"))
    for invariant in dict_items(data.get("invariants")):
        add_strings(commands, invariant.get("commands"))
    for scenario in dict_items(data.get("scenarios")):
        add_strings(commands, scenario.get("commands"))
        for probe in dict_items(scenario.get("behavioral_probes")):
            add_strings(commands, probe.get("command"))
    return unique_list(commands)


def content_mirror_files(changed_files: tuple[str, ...], *, root: Path) -> tuple[str, ...]:
    out: list[str] = []
    for raw_path in changed_files:
        normalized = normalize_source_path(raw_path, root=root).lower()
        if any(normalized.startswith(prefix) for prefix in CONTENT_PREFIXES):
            out.append(raw_path)
    return tuple(unique_list(out))


CONTENT_PREFIXES = (
    "maps/",
    "data/",
    "gfx/",
    "audio/",
    "text/",
    "scripts/",
    "engine/events/",
    "engine/gfx/",
    "engine/menus/",
    "engine/overworld/",
)


def normalize_source_path(raw_path: str, *, root: Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return raw_path.replace("\\", "/")


def expectation_failures(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report
        for report in reports
        if report.get("kind") == "unified_debugger_expectation_report"
        and report.get("passed") is False
    ]


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )


def resolve_output_dir(out_dir: str, *, root: Path) -> Path | None:
    if not out_dir:
        return None
    path = Path(out_dir)
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def display_output_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def add_strings(out: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if value:
            out.append(value)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            add_strings(out, item)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in string_items(item)
        ]
    return [str(value)] if value else []
