from __future__ import annotations

from typing import Any

from .workflow import command_is_runnable


def format_inventory(report: dict[str, Any]) -> str:
    lines = ["Unified Pokemon Gold romhack debugger inventory", f"root={report['root']}", ""]
    lines.append("Subsystems:")
    for subsystem in report["subsystems"]:
        availability = "available" if subsystem["available"] else "missing"
        lines.append(f"  - {availability}: {subsystem['id']} - {subsystem['title']}")
        lines.append(f"      scope: {subsystem['scope']}")
        for command in subsystem["entrypoints"][:2]:
            lines.append(f"      command: {command}")
    return "\n".join(lines)


def format_audit(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger capability audit",
        f"ready={report['ready']} status_counts={report['status_counts']}",
        f"blocking_gaps={report['blocking_gap_count']} gap_actions={report.get('gap_action_count', 0)}",
        "",
        "Capabilities:",
    ]
    for capability in report["capabilities"]:
        lines.append(
            f"  - {capability['status']}: {capability['id']} - {capability['title']}"
        )
        for gap in capability["gaps"][:2]:
            lines.append(f"      gap: {gap}")
        for action in capability.get("gap_actions", [])[:1]:
            lines.append(
                "      gap_action: "
                f"{action.get('id', '<unknown>')} "
                f"scenario={action.get('lived_scenario', '<unspecified>')}"
            )
            for command in action.get("commands", [])[:1]:
                lines.append(f"      proof: {command}")
        for command in capability["commands"][:1]:
            lines.append(f"      command: {command}")
    if report["blocking_gaps"]:
        lines.extend(["", "Top gaps:"])
        for gap in report["blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def format_triage(report: dict[str, Any]) -> str:
    lines = ["Unified Pokemon Gold romhack debugger triage"]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Matches:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        lines.append(f"      reason: {match['reason']}")
        for gap in match["gaps"]:
            lines.append(f"      gap: {gap}")
    lines.extend(["", "Suggested commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_next_step(report: dict[str, Any]) -> str:
    rec = report["recommendation"]
    lines = [
        "Unified Pokemon Gold romhack debugger next step",
        f"matched_lane={report['matched_lane']} symptom_class={rec['symptom_class']}",
    ]
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    lines.extend(
        [
            "",
            f"First command: {rec['first_command']}",
            "Required inputs:",
        ]
    )
    for item in rec["required_inputs"]:
        lines.append(f"  - {item}")
    lines.append("Source/data anchors:")
    for item in rec.get("source_refs", []):
        lines.append(f"  - {item}")
    lines.append("Evidence standard:")
    for item in rec.get("evidence_standard", []):
        lines.append(f"  - {item}")
    lines.append("Disproof standard:")
    for item in rec.get("disproof_standard", []):
        lines.append(f"  - {item}")
    lines.extend(
        [
            f"Proof limit: {rec['proof_limit']}",
            f"Regression gate: {rec['regression_gate']}",
            f"Escalation command: {rec['escalation_command']}",
        ]
    )
    if rec.get("repro_recipes"):
        lines.append("Repro recipes:")
        for recipe in rec["repro_recipes"]:
            lines.append(f"  - {recipe}: python -m tools.debugger repro-recipe --id {recipe}")
    if len(report["candidates"]) > 1:
        lines.extend(["", "Other matching paths:"])
        for item in report["candidates"][1:]:
            lines.append(
                f"  - {item['symptom_class']}: {item['first_command']}"
            )
    if report["triage_match_ids"]:
        lines.append("triage=" + ", ".join(report["triage_match_ids"]))
    return "\n".join(lines)


def format_proof_card(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger proof card",
        (
            f"symptom_class={report['symptom_class']} "
            f"matched_lane={report['matched_lane']} "
            f"proof_depth={report['proof_depth']} "
            f"passed={report['passed']}"
        ),
    ]
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", f"Chosen command: {report['chosen_command'] or '<none>'}"])
    execution = report.get("execution")
    if isinstance(execution, dict):
        lines.append(
            "Execution: "
            f"{execution['status']} rc={execution['returncode']} "
            f"elapsed={execution['elapsed_seconds']:.3f}s"
        )
        for line in execution.get("stdout_tail", [])[:4]:
            lines.append(f"  stdout: {line}")
        for line in execution.get("stderr_tail", [])[:4]:
            lines.append(f"  stderr: {line}")
    lines.append("Source/data anchors:")
    for item in report.get("source_refs", []):
        lines.append(f"  - {item}")
    lines.append("Evidence standard:")
    for item in report.get("evidence_standard", []):
        lines.append(f"  - {item}")
    lines.append("Disproof standard:")
    for item in report.get("disproof_standard", []):
        lines.append(f"  - {item}")
    lines.append(f"Proof limit: {report['proof_limit']}")
    lines.append(f"Regression gate: {report['regression_gate']}")
    return "\n".join(lines)


def format_proof_campaign(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger proof campaign",
        (
            f"valid={report['valid']} execute={report['execute']} "
            f"routes={report['route_row_count']} "
            f"classes={report['classified_symptom_class_count']} "
            f"commands={report['unique_command_count']} "
            f"executed={report['executed_unique_command_count']} "
            f"elapsed={report['elapsed_seconds']:.3f}s"
        ),
        f"status_counts={report['status_counts']}",
        f"blocked_reason_counts={report['blocked_reason_counts']}",
    ]
    for error in report.get("validation_errors", []):
        lines.append(f"validation_error: {error}")
    for error in report.get("expectation_errors", [])[:8]:
        lines.append(f"expectation_error: {error}")
    executed = [item for item in report["command_records"] if item["executed"]]
    if executed:
        lines.append("Executed commands:")
        for item in executed[:12]:
            execution = item.get("execution") or {}
            lines.append(
                "  - "
                f"{item['disposition']} rc={execution.get('returncode')} "
                f"{item['command']}"
            )
    blocked = [item for item in report["command_records"] if item.get("blocked_reason")]
    if blocked:
        lines.append("Blocked examples:")
        for item in blocked[:8]:
            lines.append(f"  - {item['blocked_reason']}: {item['command']}")
    return "\n".join(lines)


def format_ingest(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger ingest manifest",
        (
            f"valid={report['valid']} artifacts={report['artifact_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        "",
        "Artifacts:",
    ]
    for artifact in report["artifacts"]:
        status = "ok" if not artifact["errors"] else "error"
        lines.append(
            f"  - {status}: {artifact['kind']} {artifact['path']} "
            f"size={artifact['size_bytes']} sha256={artifact['sha256'][:12]}"
        )
        metadata = artifact["metadata"]
        if artifact["kind"] == "rom" and metadata.get("title"):
            lines.append(f"      title: {metadata['title']}")
        if artifact["kind"] == "symbols":
            lines.append(
                f"      labels: {metadata.get('label_count', 0)} "
                f"banks: {metadata.get('bank_count', 0)}"
            )
        if artifact["kind"] == "scenario":
            lines.append(
                f"      records: {metadata.get('record_count', 0)} "
                f"families: {', '.join(metadata.get('families', []))}"
            )
        if artifact["kind"] == "source_change":
            matches = metadata.get("triage_match_ids", [])
            lines.append(f"      triage: {', '.join(matches)}")
        for warning in artifact["warnings"]:
            lines.append(f"      warning: {warning}")
        for error in artifact["errors"]:
            lines.append(f"      error: {error}")
    return "\n".join(lines)


def format_gate(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger gate",
        (
            f"executed={report['executed']} passed={report['passed']} "
            f"steps={report['step_count']} failed={report['failed_count']} "
            f"skipped={report['skipped_count']}"
        ),
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Steps:"])
    for step in report["steps"]:
        runnable = "runnable" if step["runnable"] else "needs-input"
        lines.append(
            f"  - P{step['priority']} {step['status']}: {step['command']} ({runnable})"
        )
        for line in step["stderr_tail"][:2]:
            lines.append(f"      stderr: {line}")
    return "\n".join(lines)


def format_investigation_run(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger investigation run",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"steps={report['investigation_step_count']} reports={report['produced_report_count']} "
            f"findings={report['finding_count']} impact={report['impact_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report.get("out_dir"):
        lines.append(f"out_dir={report['out_dir']}")
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report.get("symbols"):
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("static_report"):
        lines.append(f"static_report={report['static_report']}")
    if report.get("visualization"):
        lines.append(f"visualization={report['visualization']}")
    next_note = report.get("symptom_only_next_step_note", "")
    if next_note:
        lines.extend(["", next_note])
    next_step = report.get("symptom_only_next_step")
    if isinstance(next_step, dict):
        lines.extend(["", *format_symptom_only_next_step(next_step)])
    lines.extend(["", "Steps:"])
    for step in report["steps"]:
        path = f" -> {step['report_path']}" if step.get("report_path") else ""
        lines.append(
            f"  - {step['status']} {step['id']} [{step['phase']}]: {step['title']}{path}"
        )
        summary = step.get("summary", {})
        if summary:
            lines.append(
                "      "
                + "; ".join(f"{key}={value}" for key, value in sorted(summary.items()))
            )
        for error in step.get("errors", [])[:2]:
            lines.append(f"      error: {error}")
        for warning in step.get("warnings", [])[:1]:
            lines.append(f"      warning: {warning}")
    if report["top_findings"]:
        lines.extend(["", "Top findings:"])
        for item in report["top_findings"][:10]:
            lines.append(
                f"  - S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']}: {item['title']}"
            )
    if report["top_impact"]:
        lines.extend(["", "Top impact:"])
        for item in report["top_impact"][:10]:
            lines.append(
                f"  - I{item['impact_score']} S{item['severity']} "
                f"{item['type']} [{item['surface']}]: {item['title']}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:10]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_symptom_only_next_step(report: dict[str, Any]) -> list[str]:
    rec = report.get("recommendation") if isinstance(report.get("recommendation"), dict) else {}
    if not rec:
        return []
    lines = [
        "Next proof path:",
        f"  - {rec.get('symptom_class', '<unknown>')}: {rec.get('title', '<unknown>')}",
        f"      first command: {rec.get('first_command', '')}",
    ]
    for source_ref in rec.get("source_refs", [])[:4]:
        lines.append(f"      source/data: {source_ref}")
    for standard in rec.get("evidence_standard", [])[:2]:
        lines.append(f"      evidence standard: {standard}")
    for standard in rec.get("disproof_standard", [])[:2]:
        lines.append(f"      disproof standard: {standard}")
    if rec.get("regression_gate"):
        lines.append(f"      regression gate: {rec['regression_gate']}")
    return lines


def format_localization_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger localization plan",
        (
            f"valid={report['valid']} candidates={report['candidate_count']} "
            f"signals={report['signal_count']} errors={report['error_count']}"
        ),
    ]
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["input_reports"]:
        lines.append("reports=" + ", ".join(report["input_reports"]))
    lines.extend(["", "Top candidates:"])
    for candidate in report["candidates"][:10]:
        lines.append(
            f"  - S{candidate['score']} {candidate['type']}: {candidate['id']}"
        )
        for evidence in candidate.get("evidence", [])[:2]:
            lines.append(f"      evidence: {evidence}")
    lines.extend(["", "Plan:"])
    for phase in report["phase_steps"]:
        lines.append(f"  {phase['title']}:")
        for step in phase["steps"][:6]:
            runnable = "runnable" if step["runnable"] else "needs-input"
            lines.append(f"    - {step['command']} ({runnable})")
            lines.append(f"        reason: {step['reason']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_coverage_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger coverage report",
        (
            f"valid={report['valid']} targets={report['target_count']} "
            f"covered={report['covered_target_count']} indirect={report['indirect_target_count']} "
            f"uncovered={report['uncovered_target_count']} ratio={report['coverage_ratio']}"
        ),
        (
            f"observed_symbols={report['covered_symbol_count']} "
            f"observed_files={report['covered_file_count']} "
            f"observed_rules={report['covered_rule_count']}"
        ),
    ]
    if report["targets"]:
        lines.extend(["", "Targets:"])
        for target in report["targets"][:30]:
            explicit = "explicit" if target["explicit"] else "related"
            lines.append(
                f"  - {target['status']} {explicit} {target['type']}: {target['id']}"
            )
            for evidence in target.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            if target["status"] == "uncovered":
                for command in target.get("commands", [])[:2]:
                    lines.append(f"      command: {command}")
    if report["covered_symbols"]:
        lines.extend(["", "Top observed symbols:"])
        for item in report["covered_symbols"][:10]:
            lines.append(f"  - {item['id']} count={item['count']}")
    if report["uncovered_targets"]:
        lines.extend(["", "Uncovered targets:"])
        for target in report["uncovered_targets"][:10]:
            lines.append(f"  - {target['type']}: {target['id']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_trace_index(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger trace index",
        (
            f"valid={report['valid']} events={report['event_count']}/{report['all_event_count']} "
            f"matched={report['matched_event_count']} writes={report['write_event_count']} "
            f"reads={report['read_event_count']} links={report['causal_link_count']} "
            f"attributions={report.get('reverse_attribution_count', 0)} "
            f"paths={report['path_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    query = report.get("query", {})
    if query.get("symbols"):
        lines.append("symbols=" + ", ".join(query["symbols"]))
    if query.get("addresses"):
        lines.append("addresses=" + ", ".join(query["addresses"]))
    if query.get("rules"):
        lines.append("rules=" + ", ".join(query["rules"]))
    if query.get("source_files"):
        lines.append("source_files=" + ", ".join(query["source_files"]))
    if query.get("symptom"):
        lines.append(f"symptom={query['symptom']}")
    if report["events"]:
        lines.extend(["", "Events:"])
        for event in report["events"][:24]:
            state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "-"
            source = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "-"
            value = ""
            if event.get("before") or event.get("after"):
                value = f" {event.get('before', '')}->{event.get('after', '')}"
            lines.append(
                f"  - {event['id']} {event['event_type']} {state} from {source}{value}"
            )
            if event.get("source_file"):
                lines.append(f"      source: {event['source_file']}")
    if report.get("reverse_attributions"):
        lines.extend(["", "Reverse attributions:"])
        for item in report["reverse_attributions"][:12]:
            lines.append(
                f"  - C{item['confidence']:.2f} {item['event_id']}: {item['title']}"
            )
            for contributor in item.get("contributors", [])[:3]:
                lines.append(
                    f"      {contributor['relation']}: {contributor['state']} "
                    f"({contributor['event_id']})"
                )
    if report["causal_paths"]:
        lines.extend(["", "Causal paths:"])
        for path in report["causal_paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} {path['id']}: {path['title']}"
            )
            for node_item in path.get("nodes", [])[:4]:
                lines.append(f"      {node_item['type']}/{node_item['role']}: {node_item['label']}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_minimization_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger minimization plan",
        (
            f"valid={report['valid']} scenarios={report['scenario_count']} "
            f"selected={report['selected_scenario_count']} errors={report['error_count']}"
        ),
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    if report["selected_scenario_ids"]:
        lines.append("selected_ids=" + ", ".join(report["selected_scenario_ids"][:10]))
    if report["bug_ids"]:
        lines.append("bug_ids=" + ", ".join(report["bug_ids"]))
    subset = report.get("subset_output", {})
    if subset.get("written"):
        lines.append(f"subset={subset['path']} records={subset['record_count']}")
    precondition_minimization = report.get("precondition_minimization", {})
    if precondition_minimization.get("attempted"):
        lines.append(
            "state_preconditions="
            + str(precondition_minimization.get("selected_precondition_count", 0))
            + "/"
            + str(precondition_minimization.get("precondition_count", 0))
        )
    state_patch_minimization = report.get("state_patch_minimization", {})
    if state_patch_minimization.get("attempted"):
        lines.append(
            "state_patches_minimized="
            + str(state_patch_minimization.get("preserved", False))
            + " "
            + str(state_patch_minimization.get("original_patch_count", 0))
            + "->"
            + str(state_patch_minimization.get("minimized_patch_count", 0))
        )
        if state_patch_minimization.get("execute_state_patches"):
            lines.append(
                "state_patch_execution="
                + str(state_patch_minimization.get("executed_candidate_count", 0))
                + "/"
                + str(state_patch_minimization.get("execution_attempt_count", 0))
            )
        if state_patch_minimization.get("out_report"):
            lines.append(f"state_patch_subset={state_patch_minimization['out_report']}")
    evidence_minimization = report.get("evidence_minimization", {})
    if evidence_minimization.get("attempted"):
        source_kind = str(evidence_minimization.get("source_kind", "trace") or "evidence")
        lines.append(
            "evidence_minimized="
            + str(evidence_minimization.get("preserved", False))
            + (
                f" {source_kind}"
                f" {evidence_minimization.get('original_count', 0)}"
                f"->{evidence_minimization.get('minimized_count', 0)}"
            )
        )
        if evidence_minimization.get("context_frame_original_count"):
            lines.append(
                "context_frames="
                + str(evidence_minimization.get("context_frame_original_count", 0))
                + "->"
                + str(evidence_minimization.get("context_frame_minimized_count", 0))
            )
        if evidence_minimization.get("out_trace"):
            lines.append(f"evidence_subset={evidence_minimization['out_trace']}")
    lines.extend(["", "Steps:"])
    for step in report["steps"][:30]:
        runnable = "runnable" if step["runnable"] else "needs-input"
        lines.append(f"  - {step['phase']}: {step['command']} ({runnable})")
        lines.append(f"      reason: {step['reason']}")
    if report["signals"]:
        lines.extend(["", "Signals:"])
        for item in report["signals"][:12]:
            lines.append(
                f"  - W{item['weight']} {item['kind']} {item['value']} ({item['type']})"
            )
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_generation_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger generation plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"generators={report['generator_count']} counterexamples={report['counterexample_count']} "
            f"seeds={report['seed_count']} errors={report['error_count']}"
        ),
        f"seed={report['seed']} max_cases={report['max_cases']}",
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["families"]:
        lines.append("families=" + ", ".join(report["families"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    seed_manifest = report.get("seed_manifest", {})
    if seed_manifest.get("written"):
        lines.append(
            f"seed_manifest={seed_manifest['path']} records={seed_manifest['record_count']}"
        )
    lines.extend(["", "Generators:"])
    for generator in report["generators"]:
        lines.append(
            f"  - {generator['id']} [{generator['surface']}] "
            f"{generator['status']} C{generator['confidence']:.2f}: {generator['title']}"
        )
        for gap in generator.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
        for command in generator.get("commands", [])[:3]:
            runnable = "runnable" if command["runnable"] else "needs-input"
            lines.append(f"      command: {command['command']} ({runnable})")
    if report["materialization_steps"]:
        lines.extend(["", "Materialization workflow:"])
        for step in report["materialization_steps"][:24]:
            runnable = "runnable" if step["runnable"] else "needs-input"
            lines.append(f"  - {step['phase']}: {step['command']} ({runnable})")
            lines.append(f"      reason: {step['reason']}")
    if report["counterexamples"]:
        lines.extend(["", "Counterexample commands:"])
        for item in report["counterexamples"][:20]:
            runnable = "runnable" if item["runnable"] else "needs-input"
            surface = f" [{item['surface']}]" if item.get("surface") else ""
            lines.append(f"  - {item['source']}{surface}: {item['command']} ({runnable})")
    if report["signals"]:
        lines.extend(["", "Signals:"])
        for item in report["signals"][:12]:
            lines.append(
                f"  - W{item['weight']} {item['kind']} {item['value']} ({item['type']})"
            )
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_fuzz_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger fuzz plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"campaigns={report['campaign_count']} dynamic={report['dynamic_campaign_count']} "
            f"static={report['static_campaign_count']} cases={report['fuzz_case_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"seed={report['seed']} max_cases={report['max_cases']}",
        "surfaces=" + ", ".join(report["surfaces"]),
    ]
    case_manifest = report.get("case_manifest", {})
    if case_manifest.get("written"):
        lines.append(f"case_manifest={case_manifest['path']} records={case_manifest['record_count']}")
    lines.extend(["", "Campaigns:"])
    for campaign in report["campaigns"]:
        lines.append(
            f"  - {campaign['id']} [{campaign['surface']}] "
            f"{campaign['status']} {campaign['proof_level']} C{campaign['confidence']:.2f}: {campaign['title']}"
        )
        for gap in campaign.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
        for command in campaign.get("commands", [])[:3]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"      command: {command} ({runnable})")
    if report["fuzz_cases"]:
        lines.extend(["", "Fuzz cases:"])
        for case in report["fuzz_cases"][:16]:
            lines.append(
                f"  - {case['id']} {case['surface']} {case['fuzz_type']} "
                f"{case['proof_level']}"
            )
            for expectation in case.get("expectations", [])[:2]:
                lines.append(f"      expect: {expectation}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_provenance(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger provenance",
        (
            f"valid={report['valid']} symbols={report['symbol_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbol_file={report['symbols_path']} sha256={report['symbols_sha256'][:12]}",
        "",
    ]
    if report["symbols"]:
        lines.append("Symbols:")
        for symbol in report["symbols"]:
            address = symbol.get("address")
            location = address["bank_address"] if address else "not-in-symbols"
            lines.append(
                f"  - {symbol['query']} {location} "
                f"source_hits={symbol['source_hit_count']}"
            )
            for hit in symbol["source_hits"][:5]:
                lines.append(
                    f"      {hit['kind']}: {hit['path']}:{hit['line']} {hit['text']}"
                )
            for command in symbol.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    if report["source_files"]:
        lines.append("Source files:")
        for source in report["source_files"]:
            lines.append(
                f"  - {source['path']} labels={source['label_count']} "
                f"symbol_matches={source['symbols_matched_count']}"
            )
            for label in source["labels"][:5]:
                address = label.get("address", {})
                suffix = f" {address.get('bank_address', '')}" if address else ""
                lines.append(f"      label: {label['label']}:{label['line']}{suffix}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_slice(report: dict[str, Any]) -> str:
    graph = report["graph"]
    lines = [
        "Unified Pokemon Gold romhack debugger causal slice",
        (
            f"valid={report['valid']} nodes={graph['node_count']} "
            f"edges={graph['edge_count']} source_files={graph['source_file_count']}"
        ),
        f"symbol_file={report['symbols_path']} sha256={report['symbols_sha256'][:12]}",
        "",
    ]
    if report["targets"]:
        lines.append("Targets:")
        for target in report["targets"]:
            if not target["found"]:
                lines.append(f"  - {target['query']} not-found")
                continue
            address = target.get("address") or {}
            location = address.get("bank_address", "source-only")
            definition = target.get("definition") or {}
            lines.append(
                f"  - {target['resolved']} {location} "
                f"defined={definition.get('path', '<unknown>')}:{definition.get('line', '?')}"
            )
            lines.append(
                f"      incoming={len(target['incoming'])} outgoing={len(target['outgoing'])} "
                f"impact_files={len(target['impact_files'])}"
            )
            for edge in target["incoming"][:8]:
                lines.append(
                    f"      in d{edge['depth']} {edge['access']}: "
                    f"{edge['source']} -> {edge['target']} "
                    f"{edge['path']}:{edge['line']} {edge['text']}"
                )
            for edge in target["outgoing"][:5]:
                lines.append(
                    f"      out d{edge['depth']} {edge['access']}: "
                    f"{edge['source']} -> {edge['target']} "
                    f"{edge['path']}:{edge['line']} {edge['text']}"
                )
            for command in target.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    if report["source_files"]:
        lines.append("Source files:")
        for source in report["source_files"]:
            lines.append(
                f"  - {source['path']} labels={source.get('label_count', 0)} "
                f"incoming={len(source.get('incoming', []))} "
                f"outgoing={len(source.get('outgoing', []))}"
            )
            for command in source.get("suggested_commands", [])[:3]:
                lines.append(f"      command: {command}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_taint(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger taint report",
        (
            f"valid={report['valid']} targets={report['target_count']} "
            f"sinks={report['sink_count']} contributors={report['contributor_count']} "
            f"paths={report['path_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbols={report['symbols_path']} sources={report['source_file_count']} routines={report['routine_count']}",
    ]
    if report["targets"]:
        lines.extend(["", "Targets:"])
        for target in report["targets"][:12]:
            lines.append(
                f"  - {target['symbol']} found={target['found']} "
                f"sinks={target['sink_count']} contributors={target['contributor_count']}"
            )
            for contributor in target.get("contributors", [])[:4]:
                lines.append(
                    f"      {contributor['relation']}: {contributor['symbol']} "
                    f"at {contributor.get('source_file', '')}:{contributor.get('line', '')}"
                )
    if report["paths"]:
        lines.extend(["", "Taint paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} "
                f"{path['target']} {path['access']} {path['source_file']}:{path['line']}"
            )
            for step in path.get("steps", [])[:4]:
                lines.append(f"      {step['role']}: {step['code']}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_dynamic_taint(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger dynamic taint report",
        (
            f"valid={report['valid']} traces={report['trace_count']} "
            f"sources={report['source_count']} sinks={report['sink_count']} "
            f"findings={report['finding_count']} paths={report['path_count']} "
            f"writes={report.get('write_attribution_count', 0)} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"symbols={report['symbols_path']}",
    ]
    if report.get("sources"):
        lines.extend(["", "Sources:"])
        for source in report["sources"][:12]:
            if source.get("type") == "register":
                lines.append(f"  - register {source.get('register')} -> {source.get('origin')}")
            else:
                lines.append(f"  - memory ${source.get('address')} -> {source.get('origin')}")
    if report.get("paths"):
        lines.extend(["", "Dynamic taint paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} "
                f"{path['title']}"
            )
            lines.append(
                f"      seq={path.get('seq')} pc=${int(path.get('pc', 0)):04X} "
                f"{path.get('mnemonic', '')}"
            )
    if report.get("write_attributions"):
        lines.extend(["", "Dynamic sink writes:"])
        for attribution in report["write_attributions"][:12]:
            lines.append(
                f"  - S{attribution.get('score', 0)} C{float(attribution.get('confidence', 0.0)):.2f} "
                f"{attribution.get('target')} at {attribution.get('pc_label')}"
            )
            lines.append(
                f"      seq={attribution.get('seq')} address=${attribution.get('address')} "
                f"{attribution.get('mnemonic', '')}"
            )
            operands = ", ".join(
                str(item)
                for item in attribution.get("evidence", [])
                if str(item).startswith("sources=")
            )
            if operands:
                lines.append(f"      {operands}")
    if report.get("trace_runs"):
        lines.extend(["", "Trace runs:"])
        for run in report["trace_runs"][:8]:
            lines.append(
                f"  - {run.get('source')} frames={run.get('frame_count', 0)} "
                f"instructions={run.get('instruction_count', 0)} "
                f"findings={run.get('finding_count', 0)} "
                f"writes={run.get('write_attribution_count', 0)} "
                f"unsupported={run.get('unsupported_count', 0)}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_instruction_trace(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger instruction trace",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"functions={report['function_count']} instructions={report['instruction_count']} "
            f"captured={report['captured_frame_count']} watches={report['watch_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} sha256={report['rom_sha256'][:12]}",
        f"symbols={report['symbols']} sha256={report['symbols_sha256'][:12]}",
    ]
    input_save_state = report.get("input_save_state", "")
    effective_save_state = report.get("effective_save_state", report.get("save_state", ""))
    if input_save_state:
        lines.append(f"save_state={input_save_state}")
    if effective_save_state and effective_save_state != input_save_state:
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={effective_save_state} source={source}")
    if report.get("trace_output", {}).get("path"):
        trace_output = report["trace_output"]
        state = "written" if trace_output.get("written") else "planned"
        lines.append(f"trace={trace_output['path']} {state} records={trace_output.get('record_count', 0)}")
    selection = report.get("target_selection")
    if isinstance(selection, dict):
        functions = ", ".join(selection.get("function_symbols", [])[:8])
        watches = ", ".join(selection.get("watch_symbols", [])[:8])
        lines.append(f"selected_functions={functions or '<none>'}")
        lines.append(f"selected_watches={watches or '<none>'}")
    validation = report.get("execution_validation")
    if isinstance(validation, dict):
        hit_functions = ", ".join(validation.get("hit_function_symbols", [])[:8])
        missing_functions = ", ".join(validation.get("missing_function_symbols", [])[:8])
        lines.append(
            "execution_validation="
            f"attempted={validation.get('attempted')} "
            f"required={validation.get('required')} "
            f"hit={validation.get('hit')} "
            f"captured_functions={validation.get('captured_function_count', 0)} "
            f"ready_for_dynamic_taint={validation.get('ready_for_dynamic_taint')}"
        )
        if hit_functions:
            lines.append(f"hit_functions={hit_functions}")
        if missing_functions:
            lines.append(f"missing_functions={missing_functions}")
    if report.get("functions"):
        lines.extend(["", "Functions:"])
        for function in report["functions"][:12]:
            lines.append(
                f"  - {function['symbol']} {function.get('bank_address', '')} "
                f"instructions={function.get('instruction_count', 0)} hooks={function.get('hook_count', 0)}"
            )
            for instruction in function.get("instructions", [])[:4]:
                lines.append(
                    f"      {instruction['bank_address']} {instruction['mnemonic']}"
                )
    if report.get("sample_records"):
        lines.extend(["", "Captured sample:"])
        for record in report["sample_records"][:8]:
            lines.append(
                f"  - seq={record.get('seq')} {record.get('pc_bank_address')} "
                f"{record.get('mnemonic')}"
            )
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:10]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_watch(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger watch replay",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"frames={report['frames']} context={report.get('context_frames', 0)} "
            f"hits={report['hit_count']} reset_events={report.get('reset_event_count', 0)} "
            f"script_state_events={report.get('script_state_event_count', 0)} "
            f"dynamic_context={report.get('dynamic_context_event_count', 0)}"
        ),
        f"rom={report['rom']} sha256={report['rom_sha256'][:12]}",
        f"symbols={report['symbols']} sha256={report['symbols_sha256'][:12]}",
    ]
    if report.get("save_state"):
        lines.append(f"save_state={report.get('save_state')}")
    if report.get("battery_save"):
        lines.append(f"battery_save={report.get('battery_save')} boot_continue={report.get('boot_continue')}")
    runtime_summary = report.get("runtime_summary") if isinstance(report.get("runtime_summary"), dict) else {}
    if runtime_summary:
        initial = runtime_summary.get("initial") if isinstance(runtime_summary.get("initial"), dict) else {}
        final = runtime_summary.get("final") if isinstance(runtime_summary.get("final"), dict) else {}
        initial_registers = initial.get("registers") if isinstance(initial.get("registers"), dict) else {}
        final_registers = final.get("registers") if isinstance(final.get("registers"), dict) else {}
        lines.append(
            "runtime "
            f"initial={initial.get('pc_bank_address', '')} sp={initial_registers.get('register_sp', '')} "
            f"final={final.get('pc_bank_address', '')} sp={final_registers.get('register_sp', '')} "
            f"inputs={runtime_summary.get('applied_input_count', 0)}"
        )
    if report.get("input_events"):
        lines.append("Inputs:")
        for event in report.get("input_events", [])[:16]:
            lines.append(
                f"  - frame={event.get('frame')} button={event.get('button')} delay={event.get('delay')}"
            )
    lines.extend(["", "Watches:"])
    for watch in report["watches"]:
        location = watch["bank_address"] if watch["found"] else "not-found"
        lines.append(f"  - {watch['name']} {location} size={watch['size']}")
        for command in watch.get("suggested_commands", [])[:2]:
            lines.append(f"      command: {command}")
    if report.get("reset_sentinel"):
        lines.append("Reset sentinel targets:")
        for target in report.get("sentinel_targets", [])[:12]:
            lines.append(f"  - {target['bank_address']} {target['name']} ({target['source']})")
    if report.get("reset_events"):
        lines.append("Reset sentinel events:")
        for event in report["reset_events"][:20]:
            context = event.get("context_symbols", {})
            context_text = " ".join(f"{key}={value}" for key, value in context.items())
            lines.append(
                f"  - frame={event['frame']} pc={event['pc_bank_address']} "
                f"{event['pc_label']} {context_text}".rstrip()
            )
            dyn = event.get("dynamic_context") if isinstance(event.get("dynamic_context"), dict) else {}
            if dyn.get("context_frame_count"):
                lines.append(f"      context: {dyn['context_frame_count']} prior frame snapshots")
    if report["events"]:
        lines.append("Events:")
        for event in report["events"][:20]:
            if event.get("event_type") == "invalid_script_state":
                lines.append(
                    f"  - frame={event['frame']} invalid_script_state "
                    f"{event.get('script', '')} pc={event['pc_bank_address']} {event['pc_label']}"
                )
                for reason in event.get("reasons", [])[:3]:
                    lines.append(f"      reason: {reason}")
            else:
                lines.append(
                    f"  - frame={event['frame']} {event['watch']} "
                    f"{event['old_hex']}->{event['new_hex']} "
                    f"pc={event['pc_bank_address']} {event['pc_label']}"
                )
            cause = event.get("source_cause") if isinstance(event.get("source_cause"), dict) else {}
            context = event.get("dynamic_context") if isinstance(event.get("dynamic_context"), dict) else {}
            if context.get("context_frame_count"):
                lines.append(
                    f"      context: {context['context_frame_count']} prior frame snapshots"
                )
            for candidate in cause.get("candidates", [])[:2]:
                lines.append(
                    f"      cause: S{candidate.get('score', 0)} "
                    f"{candidate.get('access', 'reference')} "
                    f"{candidate.get('source_file', '')}:{candidate.get('line', '')}"
                )
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_save_state_inspection(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger save-state inspection",
        (
            f"valid={report['valid']} format={report.get('state_format')} "
            f"findings={report.get('finding_count', 0)} "
            f"blocking={report.get('blocking_finding_count', 0)}"
        ),
        f"state={report.get('save_state', '')}",
        f"rom={report.get('rom', '')} banks={report.get('rom_bank_count', 0)}",
    ]
    snapshot = report.get("snapshot") if isinstance(report.get("snapshot"), dict) else {}
    cpu = snapshot.get("cpu") if isinstance(snapshot.get("cpu"), dict) else {}
    if cpu:
        lines.append(
            "cpu "
            f"pc=${cpu.get('pc', {}).get('hex', '')} "
            f"sp=${cpu.get('sp', {}).get('hex', '')}"
        )
    selected = report.get("selected_wram") if isinstance(report.get("selected_wram"), dict) else {}
    if selected:
        lines.append(
            f"wram d000_base={selected.get('d000_base')} "
            f"score={selected.get('score')} map={selected.get('map_group')}:{selected.get('map_number')}"
        )
    memory = report.get("memory") if isinstance(report.get("memory"), dict) else {}
    map_info = memory.get("map") if isinstance(memory.get("map"), dict) else {}
    if map_info:
        lines.append(
            f"map={map_info.get('name') or '<unknown>'} "
            f"coords=({map_info.get('x')},{map_info.get('y')}) "
            f"scripts={map_info.get('map_scripts_bank_live')}:{map_info.get('map_scripts_pointer_live')}"
        )
    script = memory.get("script_vm") if isinstance(memory.get("script_vm"), dict) else {}
    if script:
        lines.append(
            f"script mode={script.get('mode')} running={script.get('running')} "
            f"pc={script.get('bank')}:{script.get('pos')} stack_size={script.get('stack_size')}"
        )
        for frame in script.get("stack", [])[:5]:
            lines.append(
                f"  script_stack[{frame.get('index')}] "
                f"{frame.get('bank')}:{frame.get('address')} {frame.get('region')}"
            )
    party = memory.get("party") if isinstance(memory.get("party"), dict) else {}
    if party:
        species = ", ".join(item.get("name", "") for item in party.get("species", [])[:6])
        lines.append(f"party count={party.get('count')} species={species}")
    if report.get("findings"):
        lines.extend(["", "Findings:"])
        for item in report["findings"][:20]:
            lines.append(f"  - S{item.get('severity')} {item.get('id')}: {item.get('title')}")
            detail = item.get("detail")
            if detail:
                lines.append(f"      {detail}")
    if report.get("commands"):
        lines.extend(["", "Next commands:"])
        for command in report["commands"][:6]:
            lines.append(f"  - {command}")
    for warning in report.get("warnings", [])[:5]:
        lines.append(f"warning: {warning}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_runtime_state(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger runtime state inspection",
        (
            f"valid={report['valid']} passed={report.get('passed')} "
            f"format={report.get('state_format')} supported={report.get('state_supported')} "
            f"findings={report.get('finding_count', 0)} errors={report.get('error_count', 0)} "
            f"warnings={report.get('warning_count', 0)}"
        ),
        f"state={report.get('save_state', '')}",
        f"rom={report.get('rom', '')} sha256={str(report.get('rom_sha256', ''))[:12]}",
        f"symbols={report.get('symbols', '')} sha256={str(report.get('symbols_sha256', ''))[:12]}",
    ]
    cpu = report.get("cpu", {}) if isinstance(report.get("cpu"), dict) else {}
    if cpu.get("available"):
        lines.append(
            f"cpu pc=${cpu.get('pc_hex', '')} sp=${cpu.get('sp_hex', '')} "
            f"top_return=${cpu.get('top_stack_return_hex', '')}"
        )
    map_context = report.get("map", {}) if isinstance(report.get("map"), dict) else {}
    if map_context:
        script_range = map_context.get("script_range")
        range_text = ""
        if isinstance(script_range, dict):
            range_text = (
                f" range={int(script_range.get('bank', 0)):02X}:"
                f"{script_range.get('start_hex', '')}-{script_range.get('end_hex', '') or '????'}"
            )
        expected_bank = map_context.get("expected_script_bank")
        if isinstance(expected_bank, int):
            expected_bank_text = f"${expected_bank:02X}"
        else:
            expected_bank_text = str(expected_bank)
        lines.append(
            f"map={map_context.get('name') or map_context.get('key') or '<unknown>'} "
            f"group={map_context.get('group')} number={map_context.get('number')} "
            f"expected_bank={expected_bank_text}{range_text}"
        )
    script_vm = report.get("script_vm", {}) if isinstance(report.get("script_vm"), dict) else {}
    if script_vm:
        lines.append(
            f"script mode={script_vm.get('mode_name')} running={script_vm.get('running')} "
            f"pc={script_vm.get('bank_address')} stack_size={script_vm.get('stack_size')}"
        )
        current = script_vm.get("current") if isinstance(script_vm.get("current"), dict) else {}
        if current:
            lines.append(
                f"  current valid_exec={current.get('valid_executable_address')} "
                f"in_map_range={current.get('in_current_map_script_range')} "
                f"byte={current.get('current_byte_hex', '')} label={current.get('nearest_label', '')}"
            )
        for frame in script_vm.get("stack_frames", [])[:8]:
            lines.append(
                f"  stack[{frame.get('index')}] raw_bank=${frame.get('raw_bank_hex', '')} "
                f"pc={frame.get('bank_address', '')} valid_exec={frame.get('valid_executable_address')} "
                f"in_map_range={frame.get('in_current_map_script_range')}"
            )
    evolution = report.get("evolution_context", {}) if isinstance(report.get("evolution_context"), dict) else {}
    if evolution.get("available"):
        lines.append(
            f"evolution old=${int(evolution.get('wEvolutionOldSpecies') or 0):02X} "
            f"new=${int(evolution.get('wEvolutionNewSpecies') or 0):02X}"
        )
    trainer = report.get("trainer_context", {}) if isinstance(report.get("trainer_context"), dict) else {}
    if trainer.get("available"):
        lines.append(
            f"trainer_resume bank=${int(trainer.get('wSeenTrainerBank') or 0):02X} "
            f"after=${int(trainer.get('wScriptAfterPointer') or 0):04X} "
            f"running=${int(trainer.get('wRunningTrainerBattleScript') or 0):02X} "
            f"backup_active={trainer.get('wTrainerBattleContextBackupActive')}"
        )
    if report.get("findings"):
        lines.extend(["", "Findings:"])
        for item in report["findings"][:20]:
            lines.append(f"  - S{item.get('severity')} {item.get('id')}: {item.get('title')}")
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
    if report.get("commands"):
        lines.extend(["", "Next commands:"])
        for command in report["commands"][:8]:
            lines.append(f"  - {command}")
    for warning in report.get("warnings", [])[:5]:
        lines.append(f"warning: {warning}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_learnset_inspection(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger learnset inspection",
        f"valid={report['valid']} species={report.get('species')} level={report.get('level')}",
        "current_moves=" + ", ".join(report.get("current_moves", [])),
    ]
    available = report.get("available_level_up_moves", [])
    if available:
        lines.append("learned_up_to_level:")
        for row in available[-10:]:
            lines.append(f"  - L{row['level']}: {row['move']}")
    future = report.get("future_level_up_moves", [])
    if future:
        lines.append("next_moves:")
        for row in future[:5]:
            lines.append(f"  - L{row['level']}: {row['move']}")
    if report.get("commands"):
        lines.extend(["", "Next commands:"])
        for command in report["commands"][:4]:
            lines.append(f"  - {command}")
    return "\n".join(lines)


def format_party_inspection(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger party inspection",
        f"valid={report['valid']} save={report.get('save')} slots={report.get('slots')}",
    ]
    for mon in report.get("party", []):
        lines.append(
            f"  - {mon['species']} L{mon['level']} HP={mon['current_hp']}/{mon['max_hp']} "
            f"moves={', '.join(mon['move_names'])}"
        )
    for error in report.get("errors", []):
        lines.append(f"error slot {error.get('slot')}: {error.get('error')}")
    if report.get("commands"):
        lines.extend(["", "Next commands:"])
        for command in report["commands"][:4]:
            lines.append(f"  - {command}")
    return "\n".join(lines)


def format_grass_regrowth(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger Grass regrowth table",
        f"valid={report['valid']} max_total_hp={report.get('max_total_hp')}",
        f"full_grass={report['formula']['full_grass']}",
        f"half_grass={report['formula']['half_grass']}",
    ]
    for key, title in (("full_grass", "Full Grass"), ("half_grass", "Half Grass")):
        lines.append(f"{title} cutoffs:")
        for row in report["cutoffs"][key]:
            lines.append(f"  - {row['min_hp']}-{row['max_hp']}: {row['heals']}")
    return "\n".join(lines)


def format_script_resume_gate(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger script-resume gate",
        (
            f"valid={report['valid']} passed={report.get('passed')} "
            f"findings={report.get('finding_count', 0)} "
            f"errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}"
        ),
    ]
    if report.get("input_reports"):
        lines.append("reports=" + ", ".join(report["input_reports"][:6]))
    if report.get("findings"):
        lines.extend(["", "Findings:"])
        for item in report["findings"][:20]:
            lines.append(
                f"  - {str(item.get('severity', '')).upper()} "
                f"{item.get('id')}: {item.get('summary') or item.get('title')}"
            )
            source = item.get("source")
            if source:
                lines.append(f"      source: {source}")
    if report.get("commands"):
        lines.extend(["", "Next commands:"])
        for command in report["commands"][:6]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report.get("warnings", [])[:5]:
        lines.append(f"warning: {warning}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_wram_ownership(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger WRAM ownership",
        (
            f"valid={report['valid']} symbols={len(report.get('symbols', []))} "
            f"unions={report.get('union_count', 0)} errors={report.get('error_count', 0)} "
            f"warnings={report.get('warning_count', 0)}"
        ),
        f"source={report.get('source_file', '')}",
    ]
    for item in report.get("ownership", [])[:20]:
        same_arm = ", ".join(item.get("same_arm_labels", [])[:8])
        overlaps: list[str] = []
        for arm in item.get("other_union_arms", [])[:8]:
            overlaps.extend(str(label) for label in arm.get("labels", [])[:3])
        lines.extend(
            [
                "",
                (
                    f"{item.get('symbol')}: status={item.get('status')} risk={item.get('risk')} "
                    f"line={item.get('line')} union={item.get('union_start_line')}-{item.get('union_end_line')}"
                ),
                f"  owner arm: {same_arm}",
            ]
        )
        if overlaps:
            lines.append("  overlaps: " + ", ".join(overlaps[:16]))
    if report.get("commands"):
        lines.extend(["", "Follow-up commands:"])
        for command in report["commands"][:6]:
            lines.append(f"  - {command}")
    for warning in report.get("warnings", [])[:5]:
        lines.append(f"warning: {warning}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_wram_lifetime(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger WRAM lifetime",
        (
            f"valid={report['valid']} passed={report.get('passed')} "
            f"symbols={len(report.get('symbols', []))} findings={report.get('finding_count', 0)} "
            f"errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}"
        ),
        f"through={report.get('through')} source={report.get('source_file', '')}",
    ]
    routine = report.get("routine") if isinstance(report.get("routine"), dict) else {}
    if routine:
        lines.append(
            f"barrier={routine.get('barrier', '')} "
            f"protected={routine.get('trainer_context_protected')}"
        )
    for item in report.get("findings", [])[:12]:
        lines.extend(
            [
                "",
                f"S{item.get('severity')} {item.get('id')}: {item.get('title')}",
                f"  range: {item.get('range')} {item.get('address_range')}",
                f"  barrier: {', '.join(item.get('barriers', []))}",
            ]
        )
        overlaps = item.get("overlap_labels", [])
        if overlaps:
            lines.append("  overlaps: " + ", ".join(overlaps[:16]))
        protection = item.get("protection") if isinstance(item.get("protection"), dict) else {}
        if protection:
            lines.append(
                "  protection: "
                + ", ".join(f"{key}={value}" for key, value in protection.items())
            )
    if report.get("commands"):
        lines.extend(["", "Follow-up commands:"])
        for command in report["commands"][:6]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report.get("warnings", [])[:5]:
        lines.append(f"warning: {warning}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_wram_bank_hazards(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger WRAM bank/stack hazard scan",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"files={report['source_file_count']} findings={report['finding_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report.get("source_files"):
        lines.append("source_files=" + ", ".join(report["source_files"][:8]))
    if report.get("findings"):
        lines.extend(["", "Findings:"])
        for item in report["findings"][:30]:
            lines.append(
                f"  - S{item['severity']} {item['type']} "
                f"{item['source_file']}:{item['line']} {item['routine']}"
            )
            lines.append(f"      {item['title']}")
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
    if report.get("commands"):
        lines.extend(["", "Follow-up commands:"])
        for command in report["commands"][:6]:
            lines.append(f"  - {command}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_repro_recipe(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger repro recipes",
        f"valid={report['valid']} recipes={report['recipe_count']}",
    ]
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    for recipe in report.get("recipes", []):
        lines.extend(["", f"{recipe['id']}: {recipe['title']}", f"  purpose: {recipe['purpose']}"])
        lines.append("  inputs:")
        for item in recipe.get("inputs", [])[:6]:
            lines.append(f"    - {item}")
        lines.append("  commands:")
        for command in recipe.get("commands", [])[:8]:
            lines.append(f"    - {command}")
        lines.append(f"  proof limit: {recipe['proof_limit']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_replay_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger replay plan",
        (
            f"valid={report['valid']} phases={report['phase_count']} "
            f"watch_symbols={report['watch_symbol_count']} symbols={report['symbol_count']} "
            f"sources={report['source_file_count']} scenarios={report['scenario_id_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} symbols={report['symbols_path']} frames={report['frames']} context={report.get('context_frames', 0)}",
    ]
    if report.get("save_state"):
        lines.append(f"save_state={report['save_state']}")
    if report.get("effective_save_state") and report.get("effective_save_state") != report.get("save_state"):
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={report['effective_save_state']} source={source}")
    targets = report.get("replay_targets", {})
    if targets.get("watch_symbols"):
        lines.extend(["", "Watch targets:"])
        for symbol in targets["watch_symbols"][:12]:
            lines.append(f"  - {symbol}")
    if targets.get("source_files"):
        lines.extend(["", "Source targets:"])
        for path in targets["source_files"][:8]:
            lines.append(f"  - {path}")
    watch_report = report.get("watch_report")
    if watch_report:
        lines.extend(
            [
                "",
                (
                    f"Executed watch: valid={watch_report['valid']} "
                    f"hits={watch_report['hit_count']}"
                ),
            ]
        )
        for event in watch_report.get("events", [])[:8]:
            lines.append(
                f"  - frame={event['frame']} {event['watch']} "
                f"{event['old_hex']}->{event['new_hex']} at {event['pc_bank_address']} {event['pc_label']}"
            )
            cause = event.get("source_cause") if isinstance(event.get("source_cause"), dict) else {}
            if cause.get("candidate_count"):
                lines.append(
                    f"      source_cause_candidates={cause['candidate_count']} "
                    f"top={cause['candidates'][0].get('source_file', '')}:{cause['candidates'][0].get('line', '')}"
                )
    if report["phase_steps"]:
        lines.extend(["", "Plan:"])
        for phase in report["phase_steps"]:
            lines.append(f"  {phase['title']}:")
            for step in phase["steps"][:8]:
                runnable = "runnable" if step["runnable"] else "needs-input"
                lines.append(f"    - {step['command']} ({runnable})")
                lines.append(f"        reason: {step['reason']}")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_setup_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger setup plan",
        (
            f"valid={report['valid']} surfaces={report['surface_count']} "
            f"targets={report['target_count']} commands={report['command_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report['rom']} symbols={report['symbols_path']}",
        f"scenario_manifest={report['scenario_manifest']}",
    ]
    if report.get("effective_save_state"):
        source = report.get("save_state_discovery", {}).get("selected", {}).get("source", "")
        lines.append(f"effective_save_state={report['effective_save_state']} source={source}")
    state = report.get("state_requirements", {})
    lines.append(
        "state="
        f"save_state_supplied={state.get('save_state_supplied')} "
        f"save_state_discovered={state.get('save_state_discovered')} "
        f"requires_positioned_state={state.get('requires_positioned_state')}"
    )
    coverage = report.get("trigger_coverage", {})
    if isinstance(coverage, dict):
        lines.append(
            "trigger_coverage="
            f"covered={coverage.get('covered_target_count', 0)} "
            f"planned={coverage.get('planned_target_count', 0)} "
            f"blocked={coverage.get('blocked_target_count', 0)} "
            f"ratio={coverage.get('coverage_ratio', 0.0)}"
        )
    if report.get("surfaces"):
        lines.append(f"surfaces={', '.join(report['surfaces'])}")
    for target in report.get("targets", [])[:8]:
        lines.extend(["", f"{target.get('surface')}: {target.get('title')}"])
        target_coverage = next(
            (
                row for row in coverage.get("targets", [])
                if isinstance(row, dict) and row.get("surface") == target.get("surface")
            ),
            {},
        ) if isinstance(coverage, dict) else {}
        if target_coverage:
            lines.append(
                "  coverage="
                f"{target_coverage.get('status')} "
                f"state={target_coverage.get('state_status')} "
                f"trigger={target_coverage.get('trigger_status', {}).get('status')} "
                f"validation={target_coverage.get('validation_status', {}).get('status')}"
            )
            blockers = target_coverage.get("blockers", [])
            if blockers:
                lines.append("  blockers=" + ", ".join(str(item) for item in blockers[:6]))
        recipes = target.get("state_synthesis_recipes", [])
        if recipes:
            lines.append("  state_synthesis_recipes:")
            for recipe in recipes[:4]:
                produces = ", ".join(str(item) for item in recipe.get("produces", [])[:4])
                lines.append(
                    f"    - {recipe.get('id')} status={recipe.get('status')} produces={produces}"
                )
                for command in recipe.get("commands", [])[:2]:
                    runnable = "runnable" if command.get("runnable") else "needs-input"
                    lines.append(f"        {command.get('command')} ({runnable})")
                for precondition in recipe.get("preconditions", [])[:3]:
                    values = precondition.get("values", {}) if isinstance(precondition.get("values"), dict) else {}
                    value_text = ", ".join(
                        f"{key}={value}"
                        for key, value in values.items()
                        if value not in {"", None}
                    )
                    scenario_id = precondition.get("scenario_id", "")
                    lines.append(
                        f"        precondition: {scenario_id} {precondition.get('kind', '')} {value_text}".rstrip()
                    )
        for group_name in ("setup_commands", "state_recipe_commands", "trigger_commands", "validation_commands"):
            records = target.get(group_name, [])
            if not records:
                continue
            lines.append(f"  {group_name}:")
            for record in records[:4]:
                runnable = "runnable" if record.get("runnable") else "needs-input"
                lines.append(f"    - {record.get('command')} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_explanation(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger causal explanation",
        (
            f"valid={report['valid']} paths={report['path_count']} "
            f"events={report['dynamic_event_count']} traces={report['trace_observation_count']} "
            f"content_scenarios={report.get('content_scenario_count', 0)} "
            f"targets={report['target_symbol_count']} symbols/{report['target_file_count']} files "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report.get("target_symbols"):
        lines.append("symbols=" + ", ".join(report["target_symbols"][:10]))
    if report.get("target_files"):
        lines.append("source_files=" + ", ".join(report["target_files"][:8]))
    if report["paths"]:
        lines.extend(["", "Causal paths:"])
        for path in report["paths"][:12]:
            lines.append(
                f"  - S{path['score']} C{path['confidence']:.2f} {path['id']}: {path['title']}"
            )
            node_items = list(path.get("nodes", []))
            shown_nodes = list(node_items[:6])
            shown_node_ids = {item.get("id", "") for item in shown_nodes}
            for item in node_items:
                if item.get("id", "") in shown_node_ids:
                    continue
                if item.get("role") in {"evidence_standard", "disproof_standard", "regression_gate"}:
                    shown_nodes.append(item)
                    shown_node_ids.add(item.get("id", ""))
            for item in shown_nodes:
                location = ""
                if item.get("file"):
                    location = f" {item['file']}:{item.get('line', '')}".rstrip(":")
                lines.append(f"      {item['type']}/{item['role']}: {item['label']}{location}")
            evidence_items = list(path.get("evidence", []))
            shown_evidence = list(evidence_items[:3])
            for evidence in evidence_items:
                if evidence in shown_evidence:
                    continue
                if str(evidence).startswith(("disproof standard:", "proof limit:")):
                    shown_evidence.append(evidence)
            for evidence in shown_evidence:
                lines.append(f"      evidence: {evidence}")
            for command in path.get("commands", [])[:2]:
                lines.append(f"      next: {command}")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_test_suggestions(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger test suggestions",
        f"matches={report['match_count']}",
    ]
    if report.get("input_reports"):
        lines.append("reports=" + ", ".join(report["input_reports"]))
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    for error in report.get("errors", [])[:5]:
        lines.append(f"error: {error}")
    lines.extend(["", "Matches:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        note_limit = 12 if "next_step" in match.get("matched_by", []) else 2
        notes = match.get("notes", [])
        for note in notes[:note_limit]:
            lines.append(f"      note: {note}")
        if len(notes) > note_limit:
            lines.append(f"      note: ... {len(notes) - note_limit} more")
    lines.extend(["", "Generator/check commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    lines.extend(["", "Counterexample commands:"])
    for command in report["counterexample_commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_compare_plan(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger compare plan",
        f"matches={report['match_count']}",
    ]
    if report["changed_files"]:
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("input_reports"):
        lines.append("reports=" + ", ".join(report["input_reports"]))
    if report["symbols"]:
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report["symptom"]:
        lines.append(f"symptom={report['symptom']}")
    lines.extend(["", "Mirrors:"])
    for match in report["matches"]:
        lines.append(
            f"  - {match['id']} - {match['title']} "
            f"({', '.join(match['matched_by'])})"
        )
        lines.append(f"      confidence: {match['confidence']}")
        for gap in match.get("gaps", [])[:2]:
            lines.append(f"      gap: {gap}")
    lines.extend(["", "Compare commands:"])
    for command in report["commands"]:
        lines.append(f"  - {command}")
    lines.extend(["", "Materialization/proof commands:"])
    for command in report["materialization_commands"]:
        lines.append(f"  - {command}")
    return "\n".join(lines)


def format_content_mirror(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content mirror",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"sources={report['source_file_count']} invariants={report['invariant_count']} "
            f"rom_mirrors={report.get('rom_mirror_count', 0)} "
            f"failed={report['failed_invariant_count']} warnings={report['warning_count']} "
            f"errors={report['error_count']}"
        ),
    ]
    if report.get("rom"):
        state = "available" if report.get("rom_available") else "not-found"
        lines.append(f"rom={report.get('rom')} symbols={report.get('symbols_path')} ({state})")
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("requested_source_files"):
        lines.append("source_files=" + ", ".join(report["requested_source_files"]))
    if report["source_files"]:
        lines.extend(["", "Sources:"])
        for source in report["source_files"][:20]:
            macro_counts = source.get("macro_counts", {})
            event_counts = source.get("map_event_counts", {})
            event_summary = ", ".join(
                f"{name}={count}"
                for name, count in event_counts.items()
                if count
            )
            lines.append(
                f"  - {source['path']} labels={source.get('global_label_count', 0)} "
                f"assets={source.get('asset_count', 0)}"
            )
            if event_summary:
                lines.append(f"      map events: {event_summary}")
            if source.get("rom_mirror_count"):
                lines.append(f"      rom mirrors: {source.get('rom_mirror_count')}")
            if macro_counts.get("INCBIN"):
                lines.append(f"      incbin={macro_counts['INCBIN']}")
    if report.get("rom_mirrors"):
        lines.extend(["", "ROM mirrors:"])
        for item in report["rom_mirrors"][:12]:
            line = int(item.get("line", 0))
            location = f"{item['source_file']}:{line}" if line else str(item["source_file"])
            lines.append(f"  - {item['status']} S{item['severity']} {item['title']} ({location})")
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
    if report["failed_invariants"]:
        lines.extend(["", "Failed invariants:"])
        for item in report["failed_invariants"][:20]:
            line = int(item.get("line", 0))
            location = f"{item['source_file']}:{line}" if line else str(item["source_file"])
            lines.append(f"  - S{item['severity']} {item['type']}: {item['title']} ({location})")
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
            for command in item.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_content_scenarios(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content scenarios",
        (
            f"valid={report['valid']} scenarios={report['scenario_count']} "
            f"behavioral_probes={report.get('behavioral_probe_count', 0)} "
            f"runtime_probes={report.get('runtime_probe_count', 0)} "
            f"sources={report['source_file_count']} errors={report['error_count']} "
            f"warnings={report['warning_count']}"
        ),
    ]
    manifest = report.get("scenario_manifest", {})
    if manifest.get("written"):
        lines.append(f"manifest={manifest.get('path', '')} records={manifest.get('record_count', 0)}")
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("requested_source_files"):
        lines.append("source_files=" + ", ".join(report["requested_source_files"]))
    if report["scenarios"]:
        lines.extend(["", "Scenarios:"])
        for scenario in report["scenarios"][:20]:
            trigger = scenario.get("trigger", {})
            trigger_text = ", ".join(f"{key}={value}" for key, value in trigger.items() if value)
            lines.append(
                f"  - {scenario['id']} {scenario['scenario_type']} "
                f"{scenario['source_file']}:{scenario.get('line', 0)}"
            )
            if trigger_text:
                lines.append(f"      trigger: {trigger_text}")
            runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
            trace_symbols = runtime_targets.get("trace_symbols", [])
            watch_symbols = runtime_targets.get("watch_symbols", [])
            if trace_symbols:
                lines.append("      trace: " + ", ".join(str(symbol) for symbol in trace_symbols[:5]))
            if watch_symbols:
                lines.append("      watch: " + ", ".join(str(symbol) for symbol in watch_symbols[:5]))
            for command in scenario.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
            for probe in scenario.get("behavioral_probes", [])[:3]:
                runnable = "runnable" if probe.get("runnable") else "needs-input"
                lines.append(
                    f"      probe: {probe.get('phase')} {probe.get('command')} ({runnable})"
                )
    if report["commands"]:
        lines.extend(["", "Top scenario commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_content_state(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger content state materialization",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"scenarios={report['scenario_count']} materializations={report['materialization_count']} "
            f"patches={report['patch_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
        f"rom={report.get('rom', '')} symbols={report.get('symbols', '')}",
    ]
    if report.get("base_save_state") or report.get("out_state"):
        lines.append(f"base_state={report.get('base_save_state', '')} out_state={report.get('out_state', '')}")
    for item in report.get("materializations", [])[:12]:
        lines.extend(["", f"{item.get('scenario_id')}: {item.get('precondition_kind')} status={item.get('status')}"])
        if item.get("map_name"):
            resolution = item.get("map_resolution", {}) if isinstance(item.get("map_resolution"), dict) else {}
            lines.append(
                "  map="
                f"{item.get('map_name')} group={resolution.get('map_group', 0)} "
                f"number={resolution.get('map_number', 0)}"
            )
        for patch in item.get("patches", [])[:8]:
            lines.append(
                f"  patch {patch.get('symbol')}={patch.get('value_hex')} "
                f"@{patch.get('bank_address')}"
            )
        for error in item.get("errors", [])[:4]:
            lines.append(f"  error: {error}")
    execution = report.get("execution", {})
    if execution.get("executed"):
        lines.extend(["", f"wrote={execution.get('out_state', '')} patches={execution.get('patch_count', 0)}"])
    if report.get("commands"):
        lines.extend(["", "Commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_state_space(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger state-space materialization",
        (
            f"valid={report['valid']} executed={report['executed']} "
            f"patches={report['patch_count']} errors={report['error_count']} "
            f"warnings={report['warning_count']}"
        ),
        f"rom={report.get('rom', '')} symbols={report.get('symbols', '')}",
    ]
    if report.get("scenario_id"):
        lines.append(f"scenario={report['scenario_id']}")
    if report.get("source_files"):
        lines.append("source_files=" + ", ".join(report["source_files"]))
    if report.get("base_save_state") or report.get("out_state"):
        lines.append(f"base_state={report.get('base_save_state', '')} out_state={report.get('out_state', '')}")
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    patches = state_space.get("patches", [])
    if patches:
        lines.extend(["", "Patches:"])
        for patch in patches[:16]:
            status = patch.get("status") or patch.get("materialization_status") or "planned"
            lines.append(
                f"  - {status}: {patch.get('symbol')}={patch.get('value_hex')} "
                f"@{patch.get('bank_address')}"
            )
            if patch.get("observed_hex"):
                lines.append(
                    f"      observed={patch.get('observed_hex')} verified={patch.get('verified')}"
                )
            for error in patch.get("errors", [])[:3]:
                lines.append(f"      error: {error}")
    execution = report.get("execution", {}) if isinstance(report.get("execution"), dict) else {}
    if execution.get("executed"):
        lines.extend(["", f"wrote={execution.get('out_state', '')} patches={execution.get('patch_count', 0)}"])
    if report.get("commands"):
        lines.extend(["", "Commands:"])
        for command in report["commands"][:9]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_expectation_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger expectation report",
        (
            f"valid={report['valid']} passed={report['passed']} "
            f"expectations={report['expectation_count']} passed_count={report['passed_count']} "
            f"failed={report['failed_count']} skipped={report['skipped_count']} "
            f"events={report['evidence_event_count']} errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if (
        report.get("evidence_scenario_count")
        or report.get("evidence_state_precondition_count")
        or report.get("evidence_state_patch_count")
    ):
        lines.append(
            "state_evidence="
            + f"scenarios={report.get('evidence_scenario_count', 0)} "
            + f"preconditions={report.get('evidence_state_precondition_count', 0)} "
            + f"patches={report.get('evidence_state_patch_count', 0)}"
        )
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report["input_reports"]:
        lines.append("reports=" + ", ".join(report["input_reports"]))
    if report["input_traces"]:
        lines.append("traces=" + ", ".join(report["input_traces"]))
    if report["expectations"]:
        lines.extend(["", "Expectations:"])
        for item in report["expectations"][:30]:
            lines.append(
                f"  - {item['status']} {item['id']} "
                f"({item['type']}) observed={item['observed_count']}"
            )
            for evidence in item.get("evidence", [])[:3]:
                lines.append(f"      evidence: {evidence}")
            for command in item.get("commands", [])[:2]:
                runnable = "runnable" if command_is_runnable(command) else "needs-input"
                lines.append(f"      next: {command} ({runnable})")
    summary = report.get("evidence_summary", {})
    if summary:
        lines.extend(["", "Evidence:"])
        for key in ("symbols", "rules", "source_files", "addresses", "scenario_ids"):
            values = summary.get(key, [])
            if values:
                lines.append(f"  - {key}: " + ", ".join(values[:8]))
    if report["commands"]:
        lines.extend(["", "Top proof commands:"])
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {warning}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_ranked_findings(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger ranked findings",
        (
            f"valid={report['valid']} reports={report['report_count']} "
            f"findings={report['finding_count']} errors={report['error_count']}"
        ),
    ]
    if report["errors"]:
        lines.append("Errors:")
        for error in report["errors"][:5]:
            lines.append(f"  - {error}")
    if report["findings"]:
        lines.append("Findings:")
        for item in report["findings"][:30]:
            lines.append(
                f"  - S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']}: {item['title']}"
            )
            evidence_items = list(item.get("evidence", []))
            shown_evidence = evidence_items[:2]
            for evidence in evidence_items:
                if (
                    str(evidence).startswith(("regression_gate=", "source_ref=", "evidence_standard=", "disproof_standard="))
                    and evidence not in shown_evidence
                ):
                    shown_evidence.append(evidence)
            for evidence in shown_evidence:
                lines.append(f"      evidence: {evidence}")
            for action in item.get("next_actions", [])[:2]:
                lines.append(f"      next: {action}")
    return "\n".join(lines)


def format_impact_report(report: dict[str, Any]) -> str:
    lines = [
        "Unified Pokemon Gold romhack debugger impact report",
        (
            f"valid={report['valid']} reports={report['loaded_report_count']}/{report['report_count']} "
            f"items={report['impact_count']} commands={report['command_count']} errors={report['error_count']}"
        ),
    ]
    if report.get("changed_files"):
        lines.append("changed_files=" + ", ".join(report["changed_files"]))
    if report.get("symbols"):
        lines.append("symbols=" + ", ".join(report["symbols"]))
    if report.get("symptom"):
        lines.append(f"symptom={report['symptom']}")
    if report["errors"]:
        lines.append("Errors:")
        for error in report["errors"][:5]:
            lines.append(f"  - {error}")
    if report["items"]:
        lines.append("Impact queue:")
        for item in report["items"][:30]:
            lines.append(
                f"  - I{item['impact_score']} S{item['severity']} C{item['confidence']:.2f} "
                f"{item['type']} [{item['surface']}]: {item['title']}"
            )
            for evidence in item.get("evidence", [])[:2]:
                lines.append(f"      evidence: {evidence}")
            for action in item.get("next_actions", [])[:2]:
                lines.append(f"      next: {action}")
    if report["commands"]:
        lines.append("Top proof commands:")
        for command in report["commands"][:8]:
            runnable = "runnable" if command_is_runnable(command) else "needs-input"
            lines.append(f"  - {command} ({runnable})")
    return "\n".join(lines)


def format_static_report(report: dict[str, Any]) -> str:
    if report.get("out"):
        return "\n".join(
            [
                "Unified Pokemon Gold romhack debugger static report",
                (
                    f"valid={report['valid']} format={report['format']} "
                    f"reports={report['loaded_report_count']}/{report['requested_report_count']} "
                    f"findings={report['finding_count']} errors={report['error_count']}"
                ),
                f"out={report['out']}",
            ]
        )
    return str(report["content"])


def format_visualization(report: dict[str, Any]) -> str:
    if report.get("out"):
        return "\n".join(
            [
                "Unified Pokemon Gold romhack debugger visualization",
                (
                    f"valid={report['valid']} format={report['format']} "
                    f"reports={report['loaded_report_count']}/{report['report_count']} "
                    f"traces={report['trace_count']} timeline={report['timeline_event_count']} "
                    f"waterfall={report['waterfall_step_count']} graph={report['graph_node_count']}/{report['graph_edge_count']} "
                    f"errors={report['error_count']}"
                ),
                f"out={report['out']}",
            ]
        )
    lines = [
        "Unified Pokemon Gold romhack debugger visualization",
        (
            f"valid={report['valid']} format={report['format']} "
            f"reports={report['loaded_report_count']}/{report['report_count']} "
            f"traces={report['trace_count']} timeline={report['timeline_event_count']} "
            f"waterfall={report['waterfall_step_count']} graph={report['graph_node_count']}/{report['graph_edge_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        ),
    ]
    if report["lane_summary"]:
        lines.append("Lanes:")
        for lane in report["lane_summary"][:12]:
            lines.append(
                f"  - {lane['lane']}: count={lane['count']} max_severity={lane['max_severity']}"
            )
    if report["timeline"]:
        lines.append("Timeline:")
        for item in report["timeline"][:12]:
            lines.append(f"  - S{item['severity']} {item['lane']}/{item['type']}: {item['title']}")
    for error in report["errors"][:5]:
        lines.append(f"error: {error}")
    return "\n".join(lines)

FORMATTERS = {
    "unified_debugger_inventory": format_inventory,
    "unified_debugger_capability_report": format_audit,
    "unified_debugger_triage": format_triage,
    "unified_debugger_next_step": format_next_step,
    "unified_debugger_proof_card": format_proof_card,
    "unified_debugger_proof_campaign": format_proof_campaign,
    "unified_debugger_ingest_manifest": format_ingest,
    "unified_debugger_gate_plan": format_gate,
    "unified_debugger_investigation_run": format_investigation_run,
    "unified_debugger_localization_plan": format_localization_plan,
    "unified_debugger_coverage_report": format_coverage_report,
    "unified_debugger_trace_index": format_trace_index,
    "unified_debugger_minimization_plan": format_minimization_plan,
    "unified_debugger_generation_plan": format_generation_plan,
    "unified_debugger_fuzz_plan": format_fuzz_plan,
    "unified_debugger_provenance_report": format_provenance,
    "unified_debugger_causal_slice": format_slice,
    "unified_debugger_taint_report": format_taint,
    "unified_debugger_dynamic_taint_report": format_dynamic_taint,
    "unified_debugger_instruction_trace": format_instruction_trace,
    "unified_debugger_watch_report": format_watch,
    "unified_debugger_save_state_inspection": format_save_state_inspection,
    "unified_debugger_runtime_state_report": format_runtime_state,
    "unified_debugger_learnset_inspection": format_learnset_inspection,
    "unified_debugger_party_inspection": format_party_inspection,
    "unified_debugger_grass_regrowth_report": format_grass_regrowth,
    "unified_debugger_script_resume_gate": format_script_resume_gate,
    "unified_debugger_wram_ownership": format_wram_ownership,
    "unified_debugger_wram_lifetime_report": format_wram_lifetime,
    "unified_debugger_wram_bank_hazard_report": format_wram_bank_hazards,
    "unified_debugger_repro_recipe_report": format_repro_recipe,
    "unified_debugger_replay_plan": format_replay_plan,
    "unified_debugger_setup_plan": format_setup_plan,
    "unified_debugger_causal_explanation": format_explanation,
    "unified_debugger_test_suggestions": format_test_suggestions,
    "unified_debugger_compare_plan": format_compare_plan,
    "unified_debugger_content_mirror": format_content_mirror,
    "unified_debugger_content_scenarios": format_content_scenarios,
    "unified_debugger_content_state_materialization": format_content_state,
    "unified_debugger_state_space": format_state_space,
    "unified_debugger_expectation_report": format_expectation_report,
    "unified_debugger_ranked_findings": format_ranked_findings,
    "unified_debugger_impact_report": format_impact_report,
    "unified_debugger_static_report": format_static_report,
    "unified_debugger_visualization": format_visualization,
}
