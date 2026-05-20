from __future__ import annotations

from pathlib import Path
from typing import Any

from .address_boundary import (
    reverse_query_address_boundary_addresses,
    reverse_query_address_boundary_evidence,
    reverse_query_address_boundary_fields,
)
from .catalog import ROOT
from .coverage import load_traces
from .dynamic_taint import trace_records
from .evidence import merge_evidence_atoms
from .reporting import load_reports
from .workflow import command_address_arg, command_is_runnable


PROOF_STATUSES = {
    "planned_only",
    "state_materialized",
    "runtime_observed",
    "instruction_observed",
    "taint_proven",
    "mirror_passed",
    "mirror_failed",
}
PROOF_STATUS_ORDER = {
    "planned_only": 0,
    "state_materialized": 1,
    "mirror_passed": 2,
    "runtime_observed": 3,
    "instruction_observed": 4,
    "taint_proven": 5,
    "mirror_failed": 5,
}


def build_causal_graph_report(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    max_nodes: int = 240,
    max_edges: int = 480,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    errors = [*report_errors, *trace_errors]
    if max_nodes < 1:
        errors.append("--max-nodes must be positive")
    if max_edges < 1:
        errors.append("--max-edges must be positive")

    graph = GraphBuilder()
    for symbol in symbols:
        graph.add_node(node_id("symbol", symbol), symbol, "symbol", source="input", proof_status="planned_only")
    for address in addresses:
        graph.add_node(node_id("address", address), address, "address", source="input", proof_status="planned_only")
    for loaded in loaded_reports:
        graph.add_report(loaded)
    for loaded in loaded_traces:
        graph.add_trace(loaded)

    full_nodes = sorted(graph.nodes.values(), key=node_sort_key)
    full_edges = sorted(graph.edges.values(), key=edge_sort_key)
    paths = build_paths(nodes=graph.nodes, edges=full_edges, max_paths=80)
    commands = graph_commands(
        reports=reports,
        traces=traces,
        symbols=symbols,
        addresses=addresses,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_causal_graph",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": 0,
        "errors": errors,
        "warnings": [],
        "input_reports": [item["source"] for item in loaded_reports],
        "input_traces": [item["source"] for item in loaded_traces],
        "requested_symbols": list(symbols),
        "requested_addresses": list(addresses),
        "node_count": len(full_nodes),
        "edge_count": len(full_edges),
        "path_count": len(paths),
        "proof_status_counts": proof_status_counts([*full_nodes, *full_edges, *paths]),
        "nodes": full_nodes[:max_nodes],
        "edges": full_edges[:max_edges],
        "paths": paths,
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This graph normalizes evidence from supplied reports and traces; it does not create new runtime observations.",
            "Edges keep their source report and proof status so planned routes cannot be mistaken for observed behavior.",
            "Cross-subsystem joins are by shared symbol, address, instruction label, report source, and trace sequence; full CPU side-effect reverse execution still requires richer effect capture.",
        ],
    }


class GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def add_node(
        self,
        node_id_value: str,
        label: str,
        kind: str,
        *,
        source: str,
        proof_status: str = "planned_only",
        role: str = "",
        symbols: Any = (),
        addresses: Any = (),
        files: Any = (),
        evidence: Any = (),
        evidence_atoms: Any = (),
    ) -> dict[str, Any]:
        if not node_id_value:
            node_id_value = node_id(kind or "node", label)
        node = self.nodes.setdefault(
            node_id_value,
            {
                "id": node_id_value,
                "label": str(label or node_id_value),
                "kind": str(kind or "node"),
                "role": role,
                "proof_status": normalize_proof_status(proof_status),
                "proof_status_by_source": {},
                "proof_summary": {
                    "max": normalize_proof_status(proof_status),
                    "min": normalize_proof_status(proof_status),
                    "source_count": 0,
                },
                "sources": [],
                "related_symbols": [],
                "related_addresses": [],
                "related_files": [],
                "evidence": [],
                "evidence_atoms": [],
            },
        )
        proof = normalize_proof_status(proof_status)
        source_key = str(source or "")
        node["sources"] = unique_list([*string_items(node.get("sources")), source])
        node["related_symbols"] = unique_list([*string_items(node.get("related_symbols")), *string_items(symbols)])
        node["related_addresses"] = unique_list([*string_items(node.get("related_addresses")), *string_items(addresses)])
        node["related_files"] = unique_list([*string_items(node.get("related_files")), *string_items(files)])
        node["evidence"] = unique_list([*string_items(node.get("evidence")), *string_items(evidence)])[:10]
        node["evidence_atoms"] = merge_evidence_atoms(node.get("evidence_atoms"), evidence_atoms, limit=12)
        node["proof_status"] = strongest_proof_status([node.get("proof_status"), proof])
        proof_by_source = node.get("proof_status_by_source")
        if not isinstance(proof_by_source, dict):
            proof_by_source = {}
        if source_key:
            proof_by_source[source_key] = strongest_proof_status([proof_by_source.get(source_key), proof])
        node["proof_status_by_source"] = dict(sorted(proof_by_source.items()))
        node["proof_summary"] = proof_summary(proof_by_source.values())
        if role and not node.get("role"):
            node["role"] = role
        return node

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        relation: str,
        *,
        source: str,
        proof_status: str = "planned_only",
        evidence: Any = (),
        evidence_atoms: Any = (),
        seq: Any = None,
        confidence: Any = None,
        score: Any = None,
    ) -> dict[str, Any] | None:
        if not from_id or not to_id or not relation:
            return None
        key = (from_id, to_id, relation, source)
        edge = self.edges.setdefault(
            key,
            {
                "id": safe_id(f"{from_id}->{relation}->{to_id}@{source}"),
                "from": from_id,
                "to": to_id,
                "relation": relation,
                "source": source,
                "proof_status": normalize_proof_status(proof_status),
                "evidence": [],
                "evidence_atoms": [],
            },
        )
        edge["proof_status"] = strongest_proof_status([edge.get("proof_status"), proof_status])
        edge["evidence"] = unique_list([*string_items(edge.get("evidence")), *string_items(evidence)])[:10]
        edge["evidence_atoms"] = merge_evidence_atoms(edge.get("evidence_atoms"), evidence_atoms, limit=12)
        if seq is not None:
            edge["seq"] = seq
        if confidence is not None:
            edge["confidence"] = confidence
        if score is not None:
            edge["score"] = score
        return edge

    def add_report(self, loaded: dict[str, Any]) -> None:
        data = loaded.get("data") if isinstance(loaded.get("data"), dict) else {}
        source = str(loaded.get("source", ""))
        kind = str(data.get("kind", ""))
        report_id = node_id("report", source)
        self.add_node(report_id, source, "report", source=source, proof_status="planned_only")
        self.add_played_inputs(data, source=source, report_id=report_id)
        if kind == "unified_debugger_watch_report":
            self.add_watch_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_visual_snapshot":
            self.add_visual_snapshot_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_audio_snapshot":
            self.add_audio_snapshot_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_playtest_packet":
            self.add_playtest_packet(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_effect_trace":
            self.add_effect_trace_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_dynamic_taint_report":
            self.add_dynamic_taint_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_reverse_query":
            self.add_reverse_query_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_causal_explanation":
            self.add_causal_explanation(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_provenance_report":
            self.add_provenance_report(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_ranked_findings":
            self.add_ranked_findings(data, source=source, report_id=report_id)
        elif kind == "unified_debugger_impact_report":
            self.add_impact_report(data, source=source, report_id=report_id)
        elif is_boss_ai_report(data):
            self.add_boss_ai_report(data, source=source, report_id=report_id)
        else:
            self.add_generic_report(data, source=source, report_id=report_id)

    def add_playtest_packet(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        packet_id = str(data.get("packet_id") or source)
        packet_node = node_id("playtest_packet", packet_id)
        proof = normalize_proof_status(data.get("proof_status"))
        self.add_node(
            packet_node,
            str(data.get("symptom") or packet_id),
            "playtest_packet",
            source=source,
            proof_status=proof,
            symbols=playtest_packet_symbols(data),
            addresses=data.get("addresses"),
            files=data.get("changed_files"),
            evidence=playtest_packet_evidence(data),
        )
        self.add_edge(report_id, packet_node, "captures_playtest", source=source, proof_status=proof)
        symptom = str(data.get("symptom") or "")
        if symptom:
            symptom_node = node_id("symptom", symptom)
            self.add_node(symptom_node, symptom, "symptom", source=source, proof_status=proof, evidence=data.get("notes"))
            self.add_edge(packet_node, symptom_node, "records_symptom", source=source, proof_status=proof)
        for artifact_key, artifact_kind in (
            ("rom", "rom"),
            ("symbols", "symbols"),
            ("save_state", "save_state"),
            ("input_log", "input_log"),
            ("screenshot", "screenshot"),
        ):
            artifact = str(data.get(artifact_key) or "")
            if not artifact:
                continue
            artifact_node = node_id(artifact_kind, artifact)
            self.add_node(artifact_node, artifact, artifact_kind, source=source, proof_status=proof)
            self.add_edge(packet_node, artifact_node, f"includes_{artifact_kind}", source=source, proof_status=proof)
        for path in string_items(data.get("changed_files")):
            file_node = node_id("file", path)
            self.add_node(file_node, path, "source_file", source=source, proof_status=proof)
            self.add_edge(file_node, packet_node, "scopes_playtest", source=source, proof_status=proof)
        for symbol in playtest_packet_symbols(data):
            symbol_node = node_id("symbol", symbol)
            self.add_node(symbol_node, symbol, "symbol", source=source, proof_status=proof)
            self.add_edge(packet_node, symbol_node, "targets_symbol", source=source, proof_status=proof)
        for address in string_items(data.get("addresses")):
            address_node = node_id("address", address)
            self.add_node(address_node, address, "address", source=source, proof_status=proof, addresses=[address])
            self.add_edge(packet_node, address_node, "targets_address", source=source, proof_status=proof)
        for route in dict_items(data.get("evidence_routes")):
            route_name = str(route.get("id") or route.get("title") or "evidence_route")
            route_node = node_id("playtest_route", f"{packet_id}:{route_name}")
            route_proof = normalize_proof_status(route.get("proof_status")) or "planned_only"
            self.add_node(
                route_node,
                str(route.get("title") or route_name),
                "playtest_route",
                source=source,
                proof_status=route_proof,
                evidence=playtest_route_evidence(route),
            )
            self.add_edge(packet_node, route_node, "plans_evidence_route", source=source, proof_status="planned_only")
            produced = str(route.get("produces") or "")
            if produced:
                output_node = node_id("planned_output", produced)
                self.add_node(output_node, produced, "planned_output", source=source, proof_status="planned_only")
                self.add_edge(route_node, output_node, "produces_report", source=source, proof_status="planned_only")

    def add_watch_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for index, event in enumerate(dict_items(data.get("events"))):
            watch = str(event.get("watch") or "")
            pc_label = str(event.get("pc_label") or event.get("pc_bank_address") or "")
            event_id = node_id("watch_event", f"{source}:{index}:{watch}")
            pc_id = node_id("instruction", pc_label)
            target_id = target_node_id(watch)
            self.add_node(event_id, watch or "watch event", "watch_event", source=source, proof_status="runtime_observed", evidence=watch_event_evidence(event))
            self.add_node(pc_id, pc_label, "instruction", source=source, proof_status="runtime_observed")
            self.add_node(target_id, watch, target_kind(watch), source=source, proof_status="runtime_observed")
            self.add_edge(report_id, event_id, "contains", source=source)
            self.add_edge(pc_id, event_id, "runtime_wrote", source=source, proof_status="runtime_observed", evidence=watch_event_evidence(event), seq=event.get("frame"))
            self.add_edge(event_id, target_id, "observed_change", source=source, proof_status="runtime_observed", evidence=watch_event_evidence(event), seq=event.get("frame"))
            input_context = event.get("input_context") if isinstance(event.get("input_context"), dict) else {}
            for played in dict_items(input_context.get("played_inputs")):
                input_id = played_input_node_id(source, played)
                self.add_node(input_id, played_input_title(played), "played_input", source=source, proof_status="runtime_observed", evidence=played_input_evidence(played))
                self.add_edge(input_id, event_id, "precedes_observed_change", source=source, proof_status="runtime_observed", evidence=played_input_evidence(played), seq=event.get("frame"))

    def add_played_inputs(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for played in dict_items(data.get("played_inputs"))[:200]:
            input_id = played_input_node_id(source, played)
            self.add_node(
                input_id,
                played_input_title(played),
                "played_input",
                source=source,
                proof_status="runtime_observed",
                evidence=played_input_evidence(played),
            )
            self.add_edge(report_id, input_id, "played_input", source=source, proof_status="runtime_observed", evidence=played_input_evidence(played), seq=played.get("frame"))

    def add_visual_snapshot_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        proof = snapshot_report_proof_status(
            data,
            runtime_samples=visual_snapshot_has_runtime_samples(data),
            downgrade_reason="no_visual_runtime_samples",
        )
        snapshot_id = node_id("visual_snapshot", source)
        self.add_node(
            snapshot_id,
            "Visual/UI snapshot",
            "visual_snapshot",
            source=source,
            proof_status=proof,
            evidence=visual_snapshot_evidence(data),
        )
        self.add_edge(report_id, snapshot_id, "captures_visual_state", source=source, proof_status=proof)
        screen_frame = data.get("screen_frame") if isinstance(data.get("screen_frame"), dict) else {}
        if screen_frame:
            frame_id = node_id("visual_framebuffer", f"{source}:{screen_frame.get('sha256', '')}")
            self.add_node(
                frame_id,
                str(screen_frame.get("framebuffer") or "Framebuffer snapshot"),
                "visual_framebuffer",
                source=source,
                proof_status=proof,
                evidence=visual_framebuffer_evidence(screen_frame),
            )
            self.add_edge(snapshot_id, frame_id, "captures_framebuffer", source=source, proof_status=proof)
        for surface in dict_items(data.get("surfaces")):
            name = str(surface.get("name") or surface.get("address") or "surface")
            surface_id = node_id("visual_surface", f"{source}:{name}:{surface.get('address', '')}:{surface.get('bank', '')}")
            self.add_node(
                surface_id,
                name,
                "visual_surface",
                source=source,
                proof_status=proof,
                addresses=[str(surface.get("address", ""))],
                evidence=visual_surface_evidence(surface),
            )
            self.add_edge(snapshot_id, surface_id, "samples_surface", source=source, proof_status=proof)

    def add_audio_snapshot_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        proof = snapshot_report_proof_status(
            data,
            runtime_samples=audio_snapshot_has_runtime_samples(data),
            downgrade_reason="no_audio_runtime_samples",
        )
        snapshot_id = node_id("audio_snapshot", source)
        self.add_node(
            snapshot_id,
            "Audio snapshot",
            "audio_snapshot",
            source=source,
            proof_status=proof,
            evidence=audio_snapshot_evidence(data),
        )
        self.add_edge(report_id, snapshot_id, "captures_audio_state", source=source, proof_status=proof)
        for register in dict_items(data.get("register_details")):
            name = str(register.get("name") or register.get("address") or "audio_register")
            register_id = node_id("audio_register", f"{source}:{name}:{register.get('address', '')}")
            self.add_node(
                register_id,
                name,
                "audio_register",
                source=source,
                proof_status=proof,
                addresses=[str(register.get("address", ""))],
                evidence=audio_register_evidence(register),
            )
            self.add_edge(snapshot_id, register_id, "samples_audio_register", source=source, proof_status=proof)
        for item in dict_items(data.get("symbol_state")):
            symbol = str(item.get("symbol") or item.get("address") or "audio_symbol")
            symbol_id = node_id("audio_symbol_state", f"{source}:{symbol}:{item.get('address', '')}:{item.get('bank', '')}")
            self.add_node(
                symbol_id,
                symbol,
                "audio_symbol_state",
                source=source,
                proof_status=proof,
                addresses=[str(item.get("address", ""))],
                evidence=audio_symbol_state_evidence(item),
            )
            self.add_edge(snapshot_id, symbol_id, "samples_audio_state", source=source, proof_status=proof)
        wave = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
        if wave:
            wave_id = node_id("audio_wave_ram", f"{source}:{wave.get('address', '')}")
            self.add_node(
                wave_id,
                "Wave RAM",
                "audio_wave_ram",
                source=source,
                proof_status=proof,
                addresses=[str(wave.get("address", ""))],
                evidence=audio_wave_ram_evidence(wave),
            )
            self.add_edge(snapshot_id, wave_id, "samples_audio_wave_ram", source=source, proof_status=proof)
        sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
        if sound_buffer:
            sound_id = node_id("audio_sound_buffer", f"{source}:{sound_buffer.get('source', '')}:{sound_buffer.get('sha256', '')}")
            self.add_node(
                sound_id,
                "PyBoy sound buffer",
                "audio_sound_buffer",
                source=source,
                proof_status=proof,
                evidence=audio_sound_buffer_evidence(sound_buffer),
            )
            self.add_edge(snapshot_id, sound_id, "samples_audio_sound_buffer", source=source, proof_status=proof)

    def add_effect_trace_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for validation_index, validation in enumerate(dict_items(data.get("hook_order_validations"))):
            validation_id = node_id("hook_order_validation", f"{source}:{validation_index}:{validation.get('source', '')}")
            proof = normalize_proof_status(validation.get("proof_status")) or "planned_only"
            evidence = hook_order_validation_evidence(validation)
            self.add_node(
                validation_id,
                "Hook-order pre-instruction validation",
                "hook_order_validation",
                source=source,
                proof_status=proof,
                evidence=evidence,
            )
            self.add_edge(report_id, validation_id, "carries_hook_order_validation", source=source, proof_status=proof, evidence=evidence)
        for event in dict_items(data.get("events")):
            pc_label = str(event.get("pc_label") or event.get("pc_bank_address") or "")
            pc_id = node_id("instruction", pc_label)
            self.add_node(pc_id, pc_label, "instruction", source=source, proof_status="instruction_observed")
            self.add_edge(report_id, pc_id, "observed_instruction", source=source, proof_status="instruction_observed", seq=event.get("seq"))
            for effect_index, effect in enumerate(dict_items(event.get("effects"))):
                access = str(effect.get("access", ""))
                evidence = effect_event_evidence(effect, event)
                if access == "register_write":
                    register = str(effect.get("register") or "")
                    effect_id = node_id("register_effect", f"{source}:{event.get('seq')}:{effect_index}:{register}:{effect.get('operation', '')}")
                    register_id = node_id("register", register)
                    proof = effect_item_proof_status(effect)
                    self.add_node(
                        effect_id,
                        str(effect.get("operation") or "register write"),
                        "register_write",
                        source=source,
                        proof_status=proof,
                        evidence=evidence,
                    )
                    self.add_node(register_id, register, "register", source=source, proof_status=proof)
                    self.add_edge(pc_id, effect_id, "executes_effect", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    self.add_edge(effect_id, register_id, "writes_register", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    if effect.get("post_register_status"):
                        validation_id = node_id(
                            "post_register_validation",
                            f"{source}:{event.get('seq')}:{effect_index}:{effect.get('post_register_status', '')}:{register}:{effect.get('post_observed_pc', '')}",
                        )
                        validation_evidence = post_register_evidence(effect, event)
                        status = str(effect.get("post_register_status", ""))
                        validation_relation = "post_register_mismatch" if status == "mismatch" else "post_register_confirmed"
                        self.add_node(
                            validation_id,
                            post_register_label(effect),
                            "post_register_validation",
                            source=source,
                            proof_status=proof,
                            evidence=validation_evidence,
                        )
                        self.add_edge(effect_id, validation_id, validation_relation, source=source, proof_status=proof, evidence=validation_evidence, seq=event.get("seq"))
                        self.add_edge(validation_id, register_id, "checks_register_value", source=source, proof_status=proof, evidence=validation_evidence, seq=event.get("seq"))
                    for operand in dict_items(effect.get("source_operands")):
                        operand_id = source_operand_node_id(operand)
                        self.add_node(
                            operand_id,
                            source_operand_label(operand),
                            "operand",
                            source=source,
                            proof_status=proof,
                            evidence=source_operand_evidence(operand),
                        )
                        self.add_edge(operand_id, effect_id, "feeds_effect", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    continue
                if access == "side_effect":
                    effect_id = node_id("side_effect", f"{source}:{event.get('seq')}:{effect_index}:{effect.get('kind', '')}")
                    proof = effect_item_proof_status(effect)
                    self.add_node(
                        effect_id,
                        str(effect.get("operation") or effect.get("kind") or "side effect"),
                        "side_effect",
                        source=source,
                        proof_status=proof,
                        addresses=string_items(effect.get("trigger_address")),
                    )
                    self.add_edge(pc_id, effect_id, "triggers_side_effect", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    trigger_address = str(effect.get("trigger_address") or effect.get("address_hex") or "")
                    if trigger_address:
                        address_id = node_id("address", trigger_address)
                        self.add_node(address_id, trigger_address, "address", source=source, proof_status=proof, addresses=[trigger_address])
                        self.add_edge(effect_id, address_id, "triggered_by_address", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    continue
                if access == "unmodeled":
                    effect_id = node_id("unmodeled_effect", f"{source}:{event.get('seq')}:{effect_index}:{effect.get('kind', '')}")
                    proof = effect_item_proof_status(effect)
                    self.add_node(
                        effect_id,
                        str(effect.get("operation") or effect.get("kind") or "unmodeled effect"),
                        "unmodeled_effect",
                        source=source,
                        proof_status=proof,
                        evidence=evidence,
                    )
                    self.add_edge(pc_id, effect_id, "has_unmodeled_effect", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                    continue
                if access not in {"read", "write"}:
                    continue
                address = str(effect.get("address_hex") or effect.get("address") or "")
                if not address:
                    continue
                address_label = effect_address_label(effect)
                address_id = node_id("address", address_label)
                effect_id = node_id("effect", f"{source}:{event.get('seq')}:{effect_index}:{access}:{address}")
                proof = effect_item_proof_status(effect)
                self.add_node(
                    address_id,
                    address_label,
                    "address",
                    source=source,
                    proof_status=proof,
                    addresses=effect_related_addresses(effect),
                )
                self.add_node(
                    effect_id,
                    str(effect.get("operation") or access),
                    "effect",
                    source=source,
                    proof_status=proof,
                    addresses=effect_related_addresses(effect),
                    evidence=evidence,
                )
                relation = "writes_address" if access == "write" else "reads_address"
                self.add_edge(pc_id, effect_id, "executes_effect", source=source, proof_status=proof, seq=event.get("seq"))
                self.add_edge(effect_id, address_id, relation, source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                if effect.get("post_value_status"):
                    validation_id = node_id(
                        "post_value_validation",
                        f"{source}:{event.get('seq')}:{effect_index}:{effect.get('post_value_status', '')}:{address}:{effect.get('post_observed_pc', '')}",
                    )
                    validation_evidence = post_value_evidence(effect, event)
                    status = str(effect.get("post_value_status", ""))
                    validation_relation = "post_value_mismatch" if status == "mismatch" else "post_value_confirmed"
                    self.add_node(
                        validation_id,
                        post_value_label(effect),
                        "post_value_validation",
                        source=source,
                        proof_status=proof,
                        addresses=effect_related_addresses(effect),
                        evidence=validation_evidence,
                    )
                    self.add_edge(effect_id, validation_id, validation_relation, source=source, proof_status=proof, evidence=validation_evidence, seq=event.get("seq"))
                    self.add_edge(validation_id, address_id, "checks_address_value", source=source, proof_status=proof, evidence=validation_evidence, seq=event.get("seq"))
                for operand in dict_items(effect.get("source_operands")):
                    operand_id = source_operand_node_id(operand)
                    self.add_node(
                        operand_id,
                        source_operand_label(operand),
                        "operand",
                        source=source,
                        proof_status=proof,
                        evidence=source_operand_evidence(operand),
                    )
                    self.add_edge(operand_id, effect_id, "feeds_effect", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
            for hit_index, hit in enumerate(dict_items(event.get("watch_hits"))):
                watch = str(hit.get("watch") or "")
                if not watch:
                    continue
                address = str(hit.get("address") or "")
                bank_match = str(hit.get("bank_match") or "")
                hit_id = node_id(
                    "watch_hit",
                    f"{source}:{event.get('seq')}:{hit_index}:{watch}:{hit.get('access', '')}:{address}:{bank_match}",
                )
                watch_id = target_node_id(watch)
                evidence = watch_hit_evidence(hit, event)
                relation = "matches_watch_unverified_bank" if bank_match == "bus_address_unverified_bank" else "matches_watch"
                confidence = 0.62 if bank_match == "bus_address_unverified_bank" else 0.86
                proof = watch_hit_proof_status(hit)
                self.add_node(
                    hit_id,
                    f"{watch} {hit.get('access', '')} {address}".strip(),
                    "watch_hit",
                    source=source,
                    proof_status=proof,
                    symbols=[symbol_if_not_address(watch)],
                    addresses=[address],
                    evidence=evidence,
                )
                self.add_node(
                    watch_id,
                    watch,
                    target_kind(watch),
                    source=source,
                    proof_status=proof,
                    symbols=[symbol_if_not_address(watch)],
                    addresses=[address],
                )
                self.add_edge(pc_id, hit_id, "hits_watch", source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"))
                self.add_edge(hit_id, watch_id, relation, source=source, proof_status=proof, evidence=evidence, seq=event.get("seq"), confidence=confidence)
            for change_index, change in enumerate(dict_items(event.get("unmodeled_observed_changes"))):
                address = str(change.get("address") or "")
                if not address:
                    continue
                change_id = node_id("unmodeled_observed_change", f"{source}:{event.get('seq')}:{change_index}:{address}:{change.get('next_pc', '')}")
                address_id = node_id("address", address)
                evidence = unmodeled_change_evidence(change, event)
                self.add_node(
                    change_id,
                    f"unmodeled observed change {address}",
                    "unmodeled_observed_change",
                    source=source,
                    proof_status="instruction_observed",
                    addresses=[address],
                    evidence=evidence,
                )
                self.add_node(address_id, address, "address", source=source, proof_status="instruction_observed", addresses=[address])
                self.add_edge(pc_id, change_id, "unmodeled_observed_change", source=source, proof_status="instruction_observed", evidence=evidence, seq=event.get("seq"), confidence=0.74)
                self.add_edge(change_id, address_id, "changed_unattributed_address", source=source, proof_status="instruction_observed", evidence=evidence, seq=event.get("seq"), confidence=0.74)

    def add_dynamic_taint_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for path in dict_items(data.get("paths")):
            target = str(path.get("target") or "")
            target_id = target_node_id(target)
            path_id = node_id("taint_path", path.get("id") or f"{source}:{target}:{path.get('seq', '')}")
            proof = normalize_proof_status(path.get("proof_status")) or "taint_proven"
            self.add_node(path_id, str(path.get("title") or "taint path"), "taint_path", source=source, proof_status=proof, symbols=path.get("related_symbols"), addresses=path.get("related_addresses"), files=path.get("related_files"))
            self.add_node(target_id, target, target_kind(target), source=source, proof_status=proof)
            self.add_edge(report_id, path_id, "contains", source=source)
            self.add_edge(path_id, target_id, "proves_taint_to", source=source, proof_status=proof, evidence=path.get("evidence"), seq=path.get("seq"), confidence=path.get("confidence"), score=path.get("score"))
            for contributor in dict_items(path.get("contributors")):
                symbol = str(contributor.get("symbol") or contributor.get("address") or "")
                source_id = target_node_id(symbol)
                self.add_node(source_id, symbol, target_kind(symbol), source=source, proof_status=proof)
                self.add_edge(source_id, path_id, str(contributor.get("relation") or "taints"), source=source, proof_status=proof, evidence=path.get("evidence"), confidence=contributor.get("confidence"))
        for attribution in dict_items(data.get("write_attributions")):
            self.add_write_attribution(attribution, source=source, report_id=report_id)

    def add_write_attribution(self, attribution: dict[str, Any], *, source: str, report_id: str) -> None:
        target = str(attribution.get("target") or attribution.get("sink") or "")
        target_id = target_node_id(target)
        pc_label = str(attribution.get("pc_label") or "")
        pc_id = node_id("instruction", pc_label)
        write_id = node_id("write", attribution.get("id") or f"{source}:{target}:{attribution.get('seq', '')}")
        proof = normalize_proof_status(attribution.get("proof_status"))
        self.add_node(target_id, target, target_kind(target), source=source, proof_status=proof, symbols=attribution.get("related_symbols"), addresses=attribution.get("related_addresses"), files=attribution.get("related_files"))
        self.add_node(pc_id, pc_label, "instruction", source=source, proof_status=proof)
        self.add_node(write_id, str(attribution.get("mnemonic") or "dynamic write"), "write", source=source, proof_status=proof, symbols=attribution.get("related_symbols"), addresses=attribution.get("related_addresses"))
        self.add_edge(report_id, write_id, "contains", source=source)
        self.add_edge(pc_id, write_id, "executes", source=source, proof_status=proof, evidence=attribution.get("evidence"), seq=attribution.get("seq"))
        self.add_edge(write_id, target_id, "writes", source=source, proof_status=proof, evidence=attribution.get("evidence"), seq=attribution.get("seq"), confidence=attribution.get("confidence"), score=attribution.get("score"))
        for operand in dict_items(attribution.get("source_operands")):
            operand_id = source_operand_node_id(operand)
            self.add_node(
                operand_id,
                source_operand_label(operand),
                "register" if operand.get("kind") == "register" else "operand",
                source=source,
                proof_status=proof,
                evidence=source_operand_evidence(operand),
            )
            self.add_edge(operand_id, write_id, "feeds_write", source=source, proof_status=proof, evidence=attribution.get("evidence"), seq=attribution.get("seq"))
            operand_provenance = operand.get("register_provenance") if isinstance(operand.get("register_provenance"), dict) else {}
            if operand_provenance:
                provenance_id = self.add_register_provenance(
                    operand_provenance,
                    source=source,
                    proof_status=proof,
                    write_id=write_id,
                    write_seq=attribution.get("seq"),
                )
                self.add_edge(provenance_id, operand_id, "explains_register_operand", source=source, proof_status=proof, evidence=source_operand_evidence(operand), seq=attribution.get("seq"))
            via_register = str(operand.get("via_register") or "")
            if via_register:
                provenance = register_provenance_for_operand(operand, attribution)
                feeds_register_proof = dynamic_taint_edge_proof_status(
                    proof,
                    has_taint=bool(operand.get("origin") or operand.get("symbol")),
                )
                provenance_id = self.add_register_provenance(
                    provenance,
                    source=source,
                    proof_status=proof,
                    write_id=write_id,
                    write_seq=attribution.get("seq"),
                )
                self.add_edge(operand_id, provenance_id, "feeds_register", source=source, proof_status=feeds_register_proof, evidence=source_operand_evidence(operand), seq=operand.get("via_register_write_seq"))
        for contributor in dict_items(attribution.get("contributors")):
            symbol = str(contributor.get("symbol") or contributor.get("address") or "")
            contributor_id = target_node_id(symbol)
            self.add_node(contributor_id, symbol, target_kind(symbol), source=source, proof_status=proof)
            self.add_edge(contributor_id, write_id, str(contributor.get("relation") or "contributes"), source=source, proof_status=proof, confidence=contributor.get("confidence"))
        for provenance in dict_items(attribution.get("register_provenance")):
            provenance_id = self.add_register_provenance(
                provenance,
                source=source,
                proof_status=proof,
                write_id=write_id,
                write_seq=attribution.get("seq"),
            )
            for taint in string_items(provenance.get("taint")):
                taint_id = target_node_id(taint)
                taint_proof = dynamic_taint_edge_proof_status(proof, has_taint=True)
                self.add_node(taint_id, taint, target_kind(taint), source=source, proof_status=taint_proof)
                self.add_edge(taint_id, provenance_id, "taints_register", source=source, proof_status=taint_proof, evidence=register_provenance_evidence(provenance), seq=provenance.get("seq"))

    def add_register_provenance(
        self,
        provenance: dict[str, Any],
        *,
        source: str,
        proof_status: str,
        write_id: str,
        write_seq: Any,
    ) -> str:
        provenance_id = register_provenance_node_id(provenance)
        register = str(provenance.get("register") or "")
        register_id = node_id("register", register)
        evidence = register_provenance_evidence(provenance)
        proof = normalize_proof_status(provenance.get("proof_status")) or proof_status
        self.add_node(
            provenance_id,
            register_provenance_label(provenance),
            "register_provenance",
            source=source,
            proof_status=proof,
            evidence=evidence,
            symbols=[*string_items(provenance.get("taint")), str(provenance.get("pc_label") or "")],
        )
        if register:
            self.add_node(register_id, f"register:{register}", "register", source=source, proof_status=proof)
            self.add_edge(provenance_id, register_id, "defines_register", source=source, proof_status=proof, evidence=evidence, seq=provenance.get("seq"))
            self.add_edge(register_id, write_id, "register_feeds_write", source=source, proof_status=proof_status, evidence=evidence, seq=write_seq)
        pc_label = str(provenance.get("pc_label") or "")
        if pc_label:
            pc_id = node_id("instruction", pc_label)
            self.add_node(pc_id, pc_label, "instruction", source=source, proof_status=proof)
            self.add_edge(pc_id, provenance_id, "writes_register", source=source, proof_status=proof, evidence=evidence, seq=provenance.get("seq"))
        self.add_edge(provenance_id, write_id, "register_feeds_write", source=source, proof_status=proof_status, evidence=evidence, seq=write_seq)
        return provenance_id

    def add_reverse_query_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for result in dict_items(data.get("results")):
            target = result.get("target") if isinstance(result.get("target"), dict) else {}
            label = str(target.get("label") or target.get("symbol") or result.get("matched_address") or "")
            target_id = target_node_id(label)
            query_id = node_id("reverse_query", f"{source}:{label}:{result.get('last_writer_seq', '')}")
            proof = reverse_query_result_proof_status(result)
            address_boundary_evidence = reverse_query_address_boundary_evidence(result)
            address_boundary_fields = reverse_query_address_boundary_fields(result)
            query_node = self.add_node(
                query_id,
                f"Reverse query {label}",
                "reverse_query",
                source=source,
                proof_status=proof,
                addresses=reverse_query_address_boundary_addresses(result),
                evidence=address_boundary_evidence,
                evidence_atoms=result.get("evidence_atoms"),
            )
            query_node.update(address_boundary_fields)
            self.add_node(target_id, label, target_kind(label), source=source, proof_status=proof)
            self.add_edge(report_id, query_id, "contains", source=source)
            target_edge = self.add_edge(
                query_id,
                target_id,
                "answers_target",
                source=source,
                proof_status=proof,
                evidence=[*address_boundary_evidence, *string_items(result.get("evidence"))],
                evidence_atoms=result.get("evidence_atoms"),
            )
            if target_edge is not None:
                target_edge.update(address_boundary_fields)
            self.add_reverse_query_address_boundary(
                result,
                source=source,
                query_id=query_id,
                label=label,
                proof=proof,
            )
            last_writer = result.get("last_writer") if isinstance(result.get("last_writer"), dict) else {}
            writer_label = str(last_writer.get("pc_label") or result.get("last_writer_pc") or "")
            if writer_label:
                writer_id = node_id("instruction", writer_label)
                writer_evidence = effect_event_evidence(last_writer, {})
                self.add_node(writer_id, writer_label, "instruction", source=source, proof_status=proof)
                self.add_edge(
                    writer_id,
                    query_id,
                    "last_wrote",
                    source=source,
                    proof_status=proof,
                    evidence=result.get("evidence"),
                    evidence_atoms=result.get("evidence_atoms"),
                    seq=result.get("last_writer_seq"),
                )
                write_address = str(last_writer.get("address") or result.get("matched_address") or "")
                write_id = node_id(
                    "write",
                    f"{source}:{label}:{result.get('last_writer_seq', '')}:{last_writer.get('operation', '')}:{write_address}",
                )
                self.add_node(
                    write_id,
                    str(last_writer.get("operation") or "last write"),
                    "write",
                    source=source,
                    proof_status=proof,
                    addresses=[write_address] if write_address else [],
                    evidence=writer_evidence,
                    evidence_atoms=last_writer.get("evidence_atoms"),
                )
                self.add_edge(
                    writer_id,
                    write_id,
                    "executes",
                    source=source,
                    proof_status=proof,
                    evidence=writer_evidence,
                    evidence_atoms=last_writer.get("evidence_atoms"),
                    seq=result.get("last_writer_seq"),
                )
                last_write_edge = self.add_edge(
                    write_id,
                    query_id,
                    "answers_last_write",
                    source=source,
                    proof_status=proof,
                    evidence=[*address_boundary_evidence, *string_items(result.get("evidence"))],
                    evidence_atoms=result.get("evidence_atoms"),
                    seq=result.get("last_writer_seq"),
                )
                if last_write_edge is not None:
                    last_write_edge.update(address_boundary_fields)
                for operand in dict_items(last_writer.get("source_operands")):
                    operand_id = source_operand_node_id(operand)
                    self.add_node(
                        operand_id,
                        source_operand_label(operand),
                        "operand",
                        source=source,
                        proof_status=proof,
                        evidence=source_operand_evidence(operand),
                    )
                    self.add_edge(operand_id, write_id, "feeds_write", source=source, proof_status=proof, evidence=writer_evidence, seq=result.get("last_writer_seq"))
            checkpoint = result.get("checkpoint_validation") if isinstance(result.get("checkpoint_validation"), dict) else {}
            if checkpoint.get("checkpointed"):
                checkpoint_data = checkpoint.get("checkpoint") if isinstance(checkpoint.get("checkpoint"), dict) else {}
                checkpoint_id = node_id("trace_checkpoint", f"{source}:{label}:{checkpoint_data.get('source', '')}:{checkpoint_data.get('seq', '')}")
                checkpoint_proof = normalize_proof_status(checkpoint.get("proof_status")) or "instruction_observed"
                self.add_node(
                    checkpoint_id,
                    f"Trace checkpoint seq {checkpoint_data.get('seq', '')}",
                    "trace_checkpoint",
                    source=source,
                    proof_status=checkpoint_proof,
                    evidence=trace_checkpoint_evidence(checkpoint),
                )
                self.add_edge(checkpoint_id, query_id, "bounds_effect_span", source=source, proof_status=checkpoint_proof, evidence=trace_checkpoint_evidence(checkpoint), seq=result.get("last_writer_seq"))
            span = result.get("bounded_effect_span_validation") if isinstance(result.get("bounded_effect_span_validation"), dict) else {}
            if span:
                span_id = node_id("bounded_effect_span", f"{source}:{label}:{span.get('from_seq', '')}:{span.get('to_seq', '')}:{span.get('status', '')}")
                span_proof = normalize_proof_status(span.get("proof_status")) or "planned_only"
                self.add_node(
                    span_id,
                    f"Bounded effect span {span.get('status', '')}",
                    "bounded_effect_span",
                    source=source,
                    proof_status=span_proof,
                    evidence=bounded_effect_span_evidence(span),
                )
                self.add_edge(span_id, query_id, "checks_effect_span", source=source, proof_status=span_proof, evidence=bounded_effect_span_evidence(span), seq=result.get("last_writer_seq"))
            for route in dict_items(result.get("validation_routes")):
                route_id = node_id("reverse_validation_route", f"{source}:{label}:{route.get('id', '')}")
                route_proof = normalize_proof_status(route.get("proof_status")) or "planned_only"
                self.add_node(
                    route_id,
                    str(route.get("title") or route.get("id") or "reverse validation route"),
                    "reverse_validation_route",
                    source=source,
                    proof_status=route_proof,
                    evidence=validation_route_evidence(route),
                )
                self.add_edge(query_id, route_id, "validates_answer", source=source, proof_status=route_proof)
                produced = str(route.get("produces") or "")
                if produced:
                    output_id = node_id("planned_output", produced)
                    self.add_node(output_id, produced, "planned_output", source=source, proof_status="planned_only")
                    self.add_edge(route_id, output_id, "produces_report", source=source, proof_status="planned_only")

    def add_reverse_query_address_boundary(
        self,
        result: dict[str, Any],
        *,
        source: str,
        query_id: str,
        label: str,
        proof: str,
    ) -> None:
        requested = result.get("requested_static_address") if isinstance(result.get("requested_static_address"), dict) else {}
        observed = result.get("observed_runtime_address") if isinstance(result.get("observed_runtime_address"), dict) else {}
        boundary = result.get("address_fact_boundary") if isinstance(result.get("address_fact_boundary"), dict) else {}
        if not requested and not observed and not boundary:
            return
        boundary_evidence = reverse_query_address_boundary_evidence(result)
        boundary_fields = reverse_query_address_boundary_fields(result)
        requested_key = str(requested.get("address_key") or requested.get("address") or "")
        observed_key = str(observed.get("address_key") or observed.get("address") or "")
        requested_id = ""
        observed_id = ""
        if requested_key:
            requested_id = node_id("requested_static_address", f"{source}:{label}:{requested_key}")
            requested_node = self.add_node(
                requested_id,
                f"Requested static address {requested_key}",
                "requested_static_address",
                source=source,
                proof_status="planned_only",
                addresses=[requested_key],
                evidence=boundary_evidence,
            )
            requested_node.update(boundary_fields)
            edge = self.add_edge(
                query_id,
                requested_id,
                "requests_static_address",
                source=source,
                proof_status="planned_only",
                evidence=boundary_evidence,
            )
            if edge is not None:
                edge.update(boundary_fields)
        if observed_key:
            observed_id = node_id(
                "observed_runtime_address",
                f"{source}:{label}:{observed_key}:{result.get('last_writer_seq', '')}",
            )
            observed_proof = normalize_proof_status(observed.get("proof_status")) or proof
            observed_node = self.add_node(
                observed_id,
                f"Observed runtime address {observed_key}",
                "observed_runtime_address",
                source=source,
                proof_status=observed_proof,
                addresses=[observed_key],
                evidence=boundary_evidence,
            )
            observed_node.update(boundary_fields)
            edge = self.add_edge(
                observed_id,
                query_id,
                "supplies_runtime_address",
                source=source,
                proof_status=observed_proof,
                evidence=boundary_evidence,
            )
            if edge is not None:
                edge.update(boundary_fields)
        if requested_id and observed_id:
            boundary_proof = proof if boundary.get("exact_runtime_address_proven") is True else "planned_only"
            edge = self.add_edge(
                requested_id,
                observed_id,
                "address_fact_boundary",
                source=source,
                proof_status=boundary_proof,
                evidence=boundary_evidence,
            )
            if edge is not None:
                edge.update(boundary_fields)

    def add_causal_explanation(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for path in dict_items(data.get("paths")):
            path_id = node_id("causal_path", path.get("id") or path.get("title") or source)
            proof = normalize_proof_status(path.get("proof_status")) or "taint_proven"
            self.add_node(path_id, str(path.get("title") or "causal path"), "causal_path", source=source, proof_status=proof)
            self.add_edge(report_id, path_id, "contains", source=source)
            id_map: dict[str, str] = {}
            for item in dict_items(path.get("nodes")):
                raw_id = str(item.get("id") or item.get("label") or "")
                graph_id = node_id(str(item.get("type") or "node"), raw_id)
                id_map[raw_id] = graph_id
                self.add_node(graph_id, str(item.get("label") or raw_id), str(item.get("type") or "node"), source=source, proof_status=proof)
                self.add_edge(path_id, graph_id, "contains_node", source=source, proof_status=proof)
            for edge in dict_items(path.get("edges")):
                from_id = id_map.get(str(edge.get("from")), node_id("node", edge.get("from")))
                to_id = id_map.get(str(edge.get("to")), node_id("node", edge.get("to")))
                self.add_edge(from_id, to_id, str(edge.get("relation") or "relates"), source=source, proof_status=proof)

    def add_provenance_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for symbol_report in dict_items(data.get("symbols")):
            symbol = str(symbol_report.get("query") or "")
            symbol_id = node_id("symbol", symbol)
            self.add_node(symbol_id, symbol, "symbol", source=source, proof_status="planned_only")
            self.add_edge(report_id, symbol_id, "describes", source=source)
            for path in string_items(symbol_report.get("related_files")):
                file_id = node_id("file", path)
                self.add_node(file_id, path, "source_file", source=source, proof_status="planned_only")
                self.add_edge(symbol_id, file_id, "source_reference", source=source, evidence=[f"hits={symbol_report.get('source_hit_count', 0)}"])
        for source_report in dict_items(data.get("source_files")):
            path = str(source_report.get("path") or source_report.get("input_path") or "")
            file_id = node_id("file", path)
            self.add_node(file_id, path, "source_file", source=source, proof_status="planned_only")
            self.add_edge(report_id, file_id, "describes", source=source)
            for label in dict_items(source_report.get("labels")):
                symbol = str(label.get("label") or "")
                symbol_id = node_id("symbol", symbol)
                self.add_node(symbol_id, symbol, "symbol", source=source, proof_status="planned_only")
                self.add_edge(file_id, symbol_id, "defines_label", source=source, evidence=[f"line={label.get('line')}"])

    def add_ranked_findings(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for index, finding in enumerate(dict_items(data.get("findings"))[:80]):
            finding_id = node_id("finding", finding.get("id") or f"{source}:{index}:{finding.get('type', 'finding')}")
            proof = normalize_proof_status(finding.get("proof_status")) or "planned_only"
            self.add_node(
                finding_id,
                str(finding.get("title") or finding_id),
                str(finding.get("type") or "finding"),
                source=source,
                proof_status=proof,
                symbols=finding.get("related_symbols"),
                addresses=finding.get("related_addresses"),
                files=finding.get("related_files"),
                evidence=finding.get("evidence"),
            )
            self.add_edge(report_id, finding_id, "ranks", source=source, proof_status=proof, score=finding.get("severity"), confidence=finding.get("confidence"))

    def add_impact_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for index, item in enumerate(dict_items(data.get("items"))[:80]):
            item_id = node_id("impact", item.get("id") or f"{source}:{index}:{item.get('type', 'impact')}")
            proof = normalize_proof_status(item.get("proof_status")) or "planned_only"
            self.add_node(
                item_id,
                str(item.get("title") or item_id),
                str(item.get("type") or "impact"),
                source=source,
                proof_status=proof,
                symbols=item.get("related_symbols"),
                addresses=item.get("related_addresses"),
                files=item.get("related_files"),
                evidence=item.get("evidence"),
            )
            self.add_edge(report_id, item_id, "scores_impact", source=source, proof_status=proof, score=item.get("impact_score"), confidence=item.get("confidence"))

    def add_boss_ai_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        proof = boss_ai_proof_status(data)
        if str(data.get("source", "")) == "python_scenario_contributions":
            for trace_index, trace in enumerate(dict_items(data.get("traces"))):
                trace_node = boss_ai_trace_node_id(trace, source=source, index=trace_index)
                self.add_node(
                    trace_node,
                    boss_ai_trace_label(trace, fallback=source),
                    "boss_ai_python_contribution_trace",
                    source=source,
                    proof_status=proof,
                    evidence=boss_ai_report_evidence(trace),
                )
                self.add_edge(report_id, trace_node, "contains_boss_ai_evidence", source=source, proof_status=proof)
                self.add_boss_ai_trace_events(trace, source=source, trace_node=trace_node, proof=proof)
            return

        trace_node = boss_ai_trace_node_id(data, source=source, index=0)
        self.add_node(
            trace_node,
            boss_ai_trace_label(data, fallback=source),
            boss_ai_trace_kind(data),
            source=source,
            proof_status=proof,
            evidence=boss_ai_report_evidence(data),
        )
        self.add_edge(report_id, trace_node, "contains_boss_ai_evidence", source=source, proof_status=proof)
        chosen = data.get("chosen") if isinstance(data.get("chosen"), dict) else {}
        if chosen:
            choice_id = node_id("boss_ai_choice", f"{source}:{boss_ai_candidate_key(chosen)}")
            self.add_node(
                choice_id,
                boss_ai_candidate_label(chosen),
                "boss_ai_choice",
                source=source,
                proof_status=proof,
                evidence=boss_ai_candidate_evidence(chosen),
            )
            self.add_edge(trace_node, choice_id, "selects_action", source=source, proof_status=proof)
        self.add_boss_ai_trace_events(data, source=source, trace_node=trace_node, proof=proof)

    def add_boss_ai_trace_events(
        self,
        data: dict[str, Any],
        *,
        source: str,
        trace_node: str,
        proof: str,
    ) -> None:
        for event in dict_items(data.get("rule_entries"))[:80]:
            source_info = source_info_from_event(event)
            rule_id = boss_ai_rule_id(source_info, event)
            if not rule_id:
                continue
            rule_node = node_id("boss_ai_rule", rule_id)
            self.add_node(
                rule_node,
                rule_id,
                "boss_ai_policy_rule",
                source=source,
                proof_status=proof,
                evidence=boss_ai_source_evidence(source_info),
            )
            self.add_edge(trace_node, rule_node, "entered_policy_rule", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info), seq=event.get("index"))
            self.add_boss_ai_public_inputs(rule_node, source_info, source=source, proof=proof)

        for event in dict_items(data.get("events"))[:120]:
            event_type = str(event.get("event_type", ""))
            if event_type == "score_delta":
                self.add_boss_ai_score_delta(event, source=source, trace_node=trace_node, proof=proof)
            elif event_type == "score_rule":
                self.add_boss_ai_score_delta(decision_score_event(event), source=source, trace_node=trace_node, proof=proof)
            elif event_type == "candidate":
                candidate = candidate_from_decision_event(event)
                candidate_node = node_id("boss_ai_candidate", f"{source}:{boss_ai_candidate_key(candidate)}")
                self.add_node(
                    candidate_node,
                    boss_ai_candidate_label(candidate),
                    "boss_ai_candidate",
                    source=source,
                    proof_status=proof,
                    evidence=boss_ai_candidate_evidence(candidate),
                )
                self.add_edge(trace_node, candidate_node, "evaluates_candidate", source=source, proof_status=proof)
            elif event_type == "selector":
                selector = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
                selector_id = node_id("boss_ai_selector", f"{source}:{selector.get('best_action_id', '')}:{selector.get('second_action_id', '')}")
                self.add_node(
                    selector_id,
                    "Boss AI selector",
                    "boss_ai_selector",
                    source=source,
                    proof_status=proof,
                    evidence=boss_ai_selector_evidence(selector),
                )
                self.add_edge(trace_node, selector_id, "runs_selector", source=source, proof_status=proof, evidence=boss_ai_selector_evidence(selector))
            elif event_type == "policy_check":
                policy = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
                policy_id = node_id("boss_ai_policy_check", f"{source}:{policy.get('verdict', '')}:{policy.get('severity', '')}")
                self.add_node(
                    policy_id,
                    f"Policy {policy.get('verdict', '')}",
                    "boss_ai_policy_check",
                    source=source,
                    proof_status=proof,
                    evidence=boss_ai_policy_evidence(policy),
                )
                self.add_edge(trace_node, policy_id, "checks_policy", source=source, proof_status=proof, evidence=boss_ai_policy_evidence(policy))

        for event in dict_items(data.get("predicate_branch_entries"))[:80]:
            self.add_boss_ai_branch(event, source=source, trace_node=trace_node, proof=proof)
        for event in dict_items(data.get("public_read_probe_entries"))[:80]:
            self.add_boss_ai_public_read_probe(event, source=source, trace_node=trace_node, proof=proof)

    def add_boss_ai_score_delta(
        self,
        event: dict[str, Any],
        *,
        source: str,
        trace_node: str,
        proof: str,
    ) -> None:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        candidate = event.get("candidate") if isinstance(event.get("candidate"), dict) else {}
        delta_id = node_id(
            "boss_ai_score_delta",
            f"{source}:{event.get('index', '')}:{rule_id}:{boss_ai_candidate_key(candidate)}:{event.get('score_before', '')}->{event.get('score_after', '')}",
        )
        self.add_node(
            delta_id,
            boss_ai_score_delta_label(event, rule_id),
            "boss_ai_score_delta",
            source=source,
            proof_status=proof,
            evidence=boss_ai_score_delta_evidence(event),
        )
        self.add_edge(trace_node, delta_id, "observed_score_delta" if proof != "planned_only" else "models_score_delta", source=source, proof_status=proof, evidence=boss_ai_score_delta_evidence(event), seq=event.get("index"))
        if rule_id:
            rule_node = node_id("boss_ai_rule", rule_id)
            self.add_node(
                rule_node,
                rule_id,
                "boss_ai_policy_rule",
                source=source,
                proof_status=proof,
                evidence=boss_ai_source_evidence(source_info),
            )
            self.add_edge(rule_node, delta_id, "contributes_score_delta", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info), seq=event.get("index"))
            self.add_boss_ai_public_inputs(rule_node, source_info, source=source, proof=proof)
        if candidate:
            candidate_node = node_id("boss_ai_candidate", f"{source}:{boss_ai_candidate_key(candidate)}")
            self.add_node(
                candidate_node,
                boss_ai_candidate_label(candidate),
                "boss_ai_candidate",
                source=source,
                proof_status=proof,
                evidence=boss_ai_candidate_evidence(candidate),
            )
            self.add_edge(candidate_node, delta_id, "receives_score_delta", source=source, proof_status=proof)
            self.add_edge(delta_id, candidate_node, "changes_candidate_score", source=source, proof_status=proof, evidence=boss_ai_score_delta_evidence(event), seq=event.get("index"))

    def add_boss_ai_branch(
        self,
        event: dict[str, Any],
        *,
        source: str,
        trace_node: str,
        proof: str,
    ) -> None:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        branch_id = str(event.get("predicate_id") or event.get("branch_symbol") or source_info.get("branch_symbol") or event.get("index") or "branch")
        outcome = str(event.get("outcome", ""))
        branch_node = node_id("boss_ai_branch", f"{source}:{branch_id}:{outcome}:{event.get('index', '')}")
        self.add_node(
            branch_node,
            f"{branch_id} -> {outcome}" if outcome else branch_id,
            "boss_ai_predicate_branch",
            source=source,
            proof_status=proof,
            evidence=boss_ai_branch_evidence(event),
        )
        self.add_edge(trace_node, branch_node, "observed_predicate_branch", source=source, proof_status=proof, evidence=boss_ai_branch_evidence(event), seq=event.get("index"))
        if rule_id:
            rule_node = node_id("boss_ai_rule", rule_id)
            self.add_node(rule_node, rule_id, "boss_ai_policy_rule", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info))
            self.add_edge(rule_node, branch_node, "controls_branch", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info), seq=event.get("index"))
            self.add_boss_ai_public_inputs(rule_node, source_info, source=source, proof=proof)
        for symbol in string_items(source_info.get("dynamic_branch_legal_inputs")):
            input_node = node_id("boss_ai_public_input", symbol)
            self.add_node(input_node, symbol, "boss_ai_public_input", source=source, proof_status=proof)
            self.add_edge(input_node, branch_node, "feeds_branch", source=source, proof_status=proof)

    def add_boss_ai_public_read_probe(
        self,
        event: dict[str, Any],
        *,
        source: str,
        trace_node: str,
        proof: str,
    ) -> None:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        probe_id = str(event.get("probe_id") or source_info.get("probe_symbol") or event.get("index") or "probe")
        outcome = str(event.get("outcome", ""))
        probe_node = node_id("boss_ai_public_probe", f"{source}:{probe_id}:{outcome}:{event.get('index', '')}")
        self.add_node(
            probe_node,
            f"{probe_id} -> {outcome}" if outcome else probe_id,
            "boss_ai_public_read_probe",
            source=source,
            proof_status=proof,
            evidence=boss_ai_probe_evidence(event),
        )
        self.add_edge(trace_node, probe_node, "observed_public_read_probe", source=source, proof_status=proof, evidence=boss_ai_probe_evidence(event), seq=event.get("index"))
        if rule_id:
            rule_node = node_id("boss_ai_rule", rule_id)
            self.add_node(rule_node, rule_id, "boss_ai_policy_rule", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info))
            self.add_edge(rule_node, probe_node, "samples_public_input", source=source, proof_status=proof, evidence=boss_ai_source_evidence(source_info), seq=event.get("index"))
            self.add_boss_ai_public_inputs(rule_node, source_info, source=source, proof=proof)
        for symbol in string_items(source_info.get("dynamic_probe_legal_inputs")):
            input_node = node_id("boss_ai_public_input", symbol)
            self.add_node(input_node, symbol, "boss_ai_public_input", source=source, proof_status=proof)
            self.add_edge(input_node, probe_node, "feeds_probe", source=source, proof_status=proof)

    def add_boss_ai_public_inputs(
        self,
        rule_node: str,
        source_info: dict[str, Any],
        *,
        source: str,
        proof: str,
    ) -> None:
        public_inputs = unique_list(
            [
                *string_items(source_info.get("public_reads")),
                *string_items(source_info.get("static_public_read_hints")),
            ]
        )
        for symbol in public_inputs:
            input_node = node_id("boss_ai_public_input", symbol)
            self.add_node(input_node, symbol, "boss_ai_public_input", source=source, proof_status=proof)
            self.add_edge(input_node, rule_node, "uses_public_input", source=source, proof_status=proof)

    def add_generic_report(self, data: dict[str, Any], *, source: str, report_id: str) -> None:
        for symbol in string_items(data.get("related_symbols")) + string_items(data.get("symbols")):
            symbol_id = node_id("symbol", symbol)
            self.add_node(symbol_id, symbol, "symbol", source=source)
            self.add_edge(report_id, symbol_id, "mentions_symbol", source=source)
        for address in string_items(data.get("related_addresses")) + string_items(data.get("addresses")):
            address_id = node_id("address", address)
            self.add_node(address_id, address, "address", source=source, addresses=[address])
            self.add_edge(report_id, address_id, "mentions_address", source=source)

    def add_trace(self, loaded: dict[str, Any]) -> None:
        source = str(loaded.get("source", ""))
        trace_id = node_id("trace", source)
        self.add_node(trace_id, source, "trace", source=source, proof_status="instruction_observed")
        previous_id = ""
        for index, record in enumerate(trace_records(loaded.get("data"))[:120]):
            pc_label = str(record.get("pc_label") or record.get("label") or record.get("pc") or f"instruction_{index}")
            instruction_id = node_id("instruction", f"{source}:{record.get('seq', index)}:{pc_label}")
            self.add_node(instruction_id, pc_label, "instruction", source=source, proof_status="instruction_observed", evidence=[str(record.get("mnemonic", ""))])
            self.add_edge(trace_id, instruction_id, "contains_instruction", source=source, proof_status="instruction_observed", seq=record.get("seq", index))
            if previous_id:
                self.add_edge(previous_id, instruction_id, "next_instruction", source=source, proof_status="instruction_observed", seq=record.get("seq", index))
            previous_id = instruction_id


def build_paths(*, nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], max_paths: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    high_value_relations = {
        "proves_taint_to",
        "writes",
        "runtime_wrote",
        "last_wrote",
        "answers_last_write",
        "feeds_write",
        "feeds_register",
        "writes_register",
        "defines_register",
        "register_feeds_write",
        "taints_register",
        "explains_register_operand",
        "writes_address",
        "observed_change",
        "answers_target",
        "observed_score_delta",
        "contributes_score_delta",
        "controls_branch",
        "observed_predicate_branch",
        "observed_public_read_probe",
        "samples_public_input",
        "selects_action",
        "checks_policy",
        "post_value_mismatch",
        "unmodeled_observed_change",
        "carries_hook_order_validation",
    }
    for edge in edges:
        relation = str(edge.get("relation", ""))
        if relation not in high_value_relations and not high_value_side_effect_path(edge):
            continue
        from_node = nodes.get(str(edge.get("from")), {})
        to_node = nodes.get(str(edge.get("to")), {})
        proof = normalize_proof_status(edge.get("proof_status"))
        summary = edge_chain_proof_summary([edge])
        path = {
            "id": f"causal_graph_path_{len(out) + 1:04d}",
            "title": f"{from_node.get('label', edge.get('from'))} {relation} {to_node.get('label', edge.get('to'))}",
            "source": edge.get("source", ""),
            "relation": relation,
            "proof_status": proof,
            "proof_vector": edge_proof_vector([edge]),
            "proof_summary": summary,
            "score": path_score(proof, relation, edge.get("score"), evidence=edge.get("evidence")),
            "confidence": edge.get("confidence", proof_confidence(proof)),
            "nodes": [from_node, to_node],
            "edges": [edge],
            "evidence": string_items(edge.get("evidence"))[:6] or [f"source={edge.get('source', '')}", f"relation={relation}"],
            "related_symbols": unique_list([*string_items(from_node.get("related_symbols")), *string_items(to_node.get("related_symbols"))]),
            "related_addresses": unique_list([*string_items(from_node.get("related_addresses")), *string_items(to_node.get("related_addresses"))]),
            "related_files": unique_list([*string_items(from_node.get("related_files")), *string_items(to_node.get("related_files"))]),
            "commands": path_commands(from_node=from_node, to_node=to_node, edge=edge),
        }
        out.append(path)
    out.extend(build_register_provenance_paths(nodes=nodes, edges=edges, start_index=len(out) + 1))
    out.sort(key=lambda item: (-int(item.get("score", 0)), str(item.get("title", ""))))
    return out[:max_paths]


def build_register_provenance_paths(
    *,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    start_index: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    incoming: dict[str, list[dict[str, Any]]] = {}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        incoming.setdefault(str(edge.get("to", "")), []).append(edge)
        outgoing.setdefault(str(edge.get("from", "")), []).append(edge)
    for feed_edge in edges:
        if feed_edge.get("relation") != "register_feeds_write":
            continue
        provenance_id = str(feed_edge.get("from", ""))
        write_id = str(feed_edge.get("to", ""))
        provenance_node = nodes.get(provenance_id, {})
        if provenance_node.get("kind") != "register_provenance":
            continue
        source_edges = [
            edge
            for edge in incoming.get(provenance_id, [])
            if edge.get("relation") in {"taints_register", "feeds_register", "writes_register"}
        ]
        target_edges = [
            edge
            for edge in outgoing.get(write_id, [])
            if edge.get("relation") == "writes"
        ]
        for source_edge in source_edges:
            for target_edge in target_edges:
                chain_edges = [source_edge, feed_edge, target_edge]
                chain_nodes = unique_nodes(
                    nodes,
                    [
                        str(source_edge.get("from", "")),
                        provenance_id,
                        write_id,
                        str(target_edge.get("to", "")),
                    ],
                )
                source_node = nodes.get(str(source_edge.get("from", "")), {})
                target_node = nodes.get(str(target_edge.get("to", "")), {})
                proof = chain_proof_status(chain_edges)
                summary = edge_chain_proof_summary(chain_edges)
                evidence = unique_list(
                    evidence_item
                    for edge in chain_edges
                    for evidence_item in string_items(edge.get("evidence"))
                )[:8]
                out.append(
                    {
                        "id": f"causal_graph_path_{start_index + len(out):04d}",
                        "title": (
                            f"{source_node.get('label', source_edge.get('from'))} -> "
                            f"{provenance_node.get('label', provenance_id)} -> "
                            f"{target_node.get('label', target_edge.get('to'))}"
                        ),
                        "source": feed_edge.get("source", ""),
                        "relation": "register_provenance_chain",
                        "proof_status": proof,
                        "proof_vector": edge_proof_vector(chain_edges),
                        "proof_summary": summary,
                        "score": min(95, max(path_score(proof, "register_feeds_write", feed_edge.get("score"), evidence=evidence), 82)),
                        "confidence": chain_confidence(chain_edges),
                        "nodes": chain_nodes,
                        "edges": chain_edges,
                        "evidence": evidence or [f"source={feed_edge.get('source', '')}", "relation=register_provenance_chain"],
                        "related_symbols": related_values_from_nodes(chain_nodes, "related_symbols"),
                        "related_addresses": related_values_from_nodes(chain_nodes, "related_addresses"),
                        "related_files": related_values_from_nodes(chain_nodes, "related_files"),
                        "commands": path_commands(
                            from_node=source_node,
                            to_node=target_node,
                            edge=feed_edge,
                        ),
                    }
                )
    return out


def unique_nodes(nodes: dict[str, dict[str, Any]], node_ids: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node_id_value in node_ids:
        if not node_id_value or node_id_value in seen:
            continue
        seen.add(node_id_value)
        node = nodes.get(node_id_value)
        if node:
            out.append(node)
    return out


def chain_proof_status(edges: list[dict[str, Any]]) -> str:
    statuses = [normalize_proof_status(edge.get("proof_status")) for edge in edges]
    if any(status == "mirror_failed" for status in statuses):
        return "mirror_failed"
    return weakest_proof_status(statuses)


def edge_proof_vector(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "relation": str(edge.get("relation", "")),
            "proof_status": normalize_proof_status(edge.get("proof_status")),
            "source": str(edge.get("source", "")),
        }
        for edge in edges
    ]


def edge_chain_proof_summary(edges: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [normalize_proof_status(edge.get("proof_status")) for edge in edges]
    return {
        "max": strongest_proof_status(statuses),
        "min": weakest_proof_status(statuses),
        "status_count": len(statuses),
        "edge_count": len(edges),
    }


def chain_confidence(edges: list[dict[str, Any]]) -> float:
    values: list[float] = []
    for edge in edges:
        try:
            values.append(float(edge.get("confidence")))
        except (TypeError, ValueError):
            continue
    return min(values) if values else proof_confidence(chain_proof_status(edges))


def related_values_from_nodes(nodes: list[dict[str, Any]], key: str) -> list[str]:
    return unique_list(value for node in nodes for value in string_items(node.get(key)))


def node_sort_key(item: dict[str, Any]) -> tuple[int, int, str, str]:
    input_priority = 0 if "input" in string_items(item.get("sources")) else 1
    kind_priority = {
        "report": 0,
        "playtest_packet": 1,
        "symptom": 2,
        "save_state": 3,
        "symbol": 4,
        "instruction": 5,
        "watch_event": 6,
        "side_effect": 7,
        "post_value_validation": 8,
        "unmodeled_observed_change": 8,
        "hook_order_validation": 8,
        "taint_path": 8,
        "causal_path": 9,
        "write": 10,
        "register_provenance": 11,
        "register": 12,
        "effect": 13,
        "operand": 14,
        "address": 15,
    }.get(str(item.get("kind", "")), 20)
    return (input_priority, kind_priority, str(item.get("label", "")), str(item.get("id", "")))


def edge_sort_key(item: dict[str, Any]) -> tuple[int, int, str, str, str]:
    proof_priority = {
        "taint_proven": 0,
        "runtime_observed": 1,
        "instruction_observed": 2,
        "state_materialized": 3,
        "mirror_failed": 4,
        "mirror_passed": 5,
        "planned_only": 6,
    }.get(normalize_proof_status(item.get("proof_status")), 9)
    relation_priority = {
        "runtime_wrote": 0,
        "observed_change": 1,
        "post_value_mismatch": 2,
        "unmodeled_observed_change": 3,
        "changed_unattributed_address": 4,
        "carries_hook_order_validation": 5,
        "proves_taint_to": 6,
        "last_wrote": 7,
        "answers_last_write": 8,
        "feeds_write": 9,
        "register_feeds_write": 10,
        "feeds_register": 11,
        "writes_register": 12,
        "defines_register": 13,
        "taints_register": 14,
        "explains_register_operand": 15,
        "triggers_side_effect": 16,
        "triggered_by_address": 17,
        "executes": 18,
        "writes": 19,
        "writes_address": 20,
        "reads_address": 21,
        "post_value_confirmed": 22,
        "checks_address_value": 23,
        "feeds_effect": 24,
        "executes_effect": 25,
        "observed_instruction": 26,
        "contains": 27,
    }.get(str(item.get("relation", "")), 20)
    return (
        proof_priority,
        relation_priority,
        str(item.get("source", "")),
        str(item.get("from", "")),
        str(item.get("to", "")),
    )


def graph_commands(*, reports: tuple[str, ...], traces: tuple[str, ...], symbols: tuple[str, ...], addresses: tuple[str, ...]) -> list[str]:
    commands = []
    if reports:
        report_args = " ".join(f"--report {quote_arg(report)}" for report in reports[:6])
        commands.append(f"python -m tools.debugger rank {report_args}")
        commands.append(f"python -m tools.debugger visualize {report_args}")
        commands.append(f"python -m tools.debugger report {report_args} --out .local\\tmp\\causal_graph_report.md")
    for symbol in symbols[:4]:
        commands.append(f"python -m tools.debugger provenance --symbol {quote_arg(symbol)}")
        commands.append(f"python -m tools.debugger explain --symbol {quote_arg(symbol)}")
    for address in addresses[:4]:
        commands.append(f"python -m tools.debugger reverse-query --report <effect-trace.json> --address {command_address_arg(address)}")
    for trace in traces[:3]:
        commands.append(f"python -m tools.debugger effect-trace --trace {quote_arg(trace)} --out-effects .local\\tmp\\causal_graph_effects.jsonl")
    return unique_list(commands)


def path_commands(*, from_node: dict[str, Any], to_node: dict[str, Any], edge: dict[str, Any]) -> list[str]:
    commands = []
    source = str(edge.get("source") or "")
    if source:
        commands.append(f"python -m tools.debugger provenance --report {quote_arg(source)}")
        commands.append(f"python -m tools.debugger visualize --report {quote_arg(source)}")
    for node in (from_node, to_node):
        if node.get("kind") == "symbol" and node.get("label"):
            commands.append(f"python -m tools.debugger explain --symbol {quote_arg(str(node['label']))}")
        for address in string_items(node.get("related_addresses"))[:2]:
            commands.append(f"python -m tools.debugger reverse-query --report <effect-trace.json> --address {command_address_arg(address)}")
    return unique_list(commands)[:8]


def path_score(proof_status: str, relation: str, raw_score: Any, *, evidence: Any = ()) -> int:
    parsed = positive_int(raw_score)
    if parsed:
        return min(95, parsed)
    base = {
        "taint_proven": 88,
        "instruction_observed": 78,
        "runtime_observed": 74,
        "state_materialized": 58,
        "mirror_failed": 86,
        "mirror_passed": 54,
        "planned_only": 40,
    }.get(proof_status, 40)
    if relation in {"proves_taint_to", "last_wrote", "answers_last_write", "feeds_write", "register_feeds_write", "taints_register"}:
        base += 4
    if relation in {"feeds_register", "writes_register", "defines_register", "explains_register_operand"}:
        base += 2
    if relation == "post_value_mismatch":
        base += 8
    if relation == "unmodeled_observed_change":
        base += 6
    if relation == "carries_hook_order_validation":
        base += 5
    if relation == "triggers_side_effect":
        base += side_effect_path_bonus(evidence)
    return min(95, base)


def high_value_side_effect_path(edge: dict[str, Any]) -> bool:
    return str(edge.get("relation", "")) == "triggers_side_effect" and side_effect_path_bonus(edge.get("evidence")) > 0


def side_effect_path_bonus(evidence: Any) -> int:
    text = "\n".join(string_items(evidence)).lower()
    if "kind=cpu_state" in text or "category=cpu" in text:
        return 8
    if "kind=interrupt_entry" in text or "kind=ime" in text or "category=interrupt" in text:
        return 5
    return 0


def proof_confidence(proof_status: str) -> float:
    return {
        "taint_proven": 0.9,
        "instruction_observed": 0.84,
        "runtime_observed": 0.8,
        "state_materialized": 0.72,
        "mirror_failed": 0.86,
        "mirror_passed": 0.72,
        "planned_only": 0.5,
    }.get(proof_status, 0.5)


def watch_event_evidence(event: dict[str, Any]) -> list[str]:
    input_context = event.get("input_context") if isinstance(event.get("input_context"), dict) else {}
    last_input = input_context.get("last_input") if isinstance(input_context.get("last_input"), dict) else {}
    return unique_list(
        [
            f"frame={event.get('frame')}",
            f"pc={event.get('pc_bank_address', '')}",
            f"{event.get('old_hex', '')}->{event.get('new_hex', '')}",
            f"last_input={played_input_title(last_input)}" if last_input else "",
        ]
    )


def played_input_node_id(source: str, played: dict[str, Any]) -> str:
    buttons = "+".join(string_items(played.get("buttons"))) or "wait"
    return node_id("played_input", f"{source}:{played.get('frame', '')}:{played.get('line', '')}:{buttons}")


def played_input_title(played: dict[str, Any]) -> str:
    buttons = "+".join(string_items(played.get("buttons")))
    if not buttons:
        return f"wait frame {played.get('frame', '')}"
    return f"input {buttons} frame {played.get('frame', '')}"


def played_input_evidence(played: dict[str, Any]) -> list[str]:
    buttons = "+".join(string_items(played.get("buttons")))
    return unique_list(
        [
            f"frame={played.get('frame')}",
            f"buttons={buttons}" if buttons else "wait=true",
            f"hold_frames={played.get('hold_frames', '')}" if played.get("hold_frames") else "",
            f"line={played.get('line', '')}" if played.get("line") else "",
            f"source={played.get('source', '')}" if played.get("source") else "",
        ]
    )


def watch_hit_evidence(hit: dict[str, Any], event: dict[str, Any]) -> list[str]:
    value_hex = str(hit.get("value_hex", ""))
    return unique_list(
        [
            f"seq={event.get('seq')}",
            f"pc={event.get('pc_bank_address', '')}",
            f"pc_label={event.get('pc_label', '')}",
            f"watch={hit.get('watch', '')}",
            f"access={hit.get('access', '')}",
            f"address={hit.get('address', '')}",
            f"bank_match={hit.get('bank_match', '')}" if hit.get("bank_match") else "",
            f"bank_source={hit.get('bank_source', '')}" if hit.get("bank_source") else "",
            f"value=0x{value_hex}" if value_hex else "",
            f"operation={hit.get('operation', '')}" if hit.get("operation") else "",
            f"watch_key={hit.get('watch_key', '')}" if hit.get("watch_key") else "",
            f"effect_key={hit.get('effect_key', '')}" if hit.get("effect_key") else "",
            f"evidence_source={hit.get('effect_evidence_source', '')}" if hit.get("effect_evidence_source") else "",
            f"evidence_status={hit.get('effect_evidence_status', '')}" if hit.get("effect_evidence_status") else "",
        ]
    )


def unmodeled_change_evidence(change: dict[str, Any], event: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"seq={change.get('seq', event.get('seq'))}",
            f"pc={change.get('pc') or event.get('pc_bank_address', '')}",
            f"pc_label={change.get('pc_label') or event.get('pc_label', '')}",
            f"address={change.get('address', '')}",
            f"old=0x{change.get('old_value_hex', '')}" if change.get("old_value_hex") else "",
            f"new=0x{change.get('new_value_hex', '')}" if change.get("new_value_hex") else "",
            f"next_seq={change.get('next_seq', '')}" if change.get("next_seq") not in {None, ""} else "",
            f"next_pc={change.get('next_pc', '')}" if change.get("next_pc") else "",
            f"status={change.get('status', '')}" if change.get("status") else "",
            str(change.get("message", "")),
        ]
    )


def hook_order_validation_evidence(validation: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"source={validation.get('source', '')}" if validation.get("source") else "",
            f"executed={bool(validation.get('executed'))}",
            f"passed={bool(validation.get('passed'))}",
            f"proof_status={validation.get('proof_status', '')}",
            f"observations={validation.get('observation_count', 0)}/{validation.get('expected_target_count', 0)}",
            f"checks={validation.get('check_count', 0)}",
            f"failed_checks={','.join(string_items(validation.get('failed_checks')))}"
            if validation.get("failed_checks")
            else "",
        ]
    )


def effect_evidence(effect: dict[str, Any]) -> list[str]:
    value_hex = str(effect.get("value_hex", ""))
    return unique_list(
        [
            str(effect.get("operation", "")),
            f"address={effect.get('address_hex') or effect.get('address') or ''}",
            f"address_key={effect.get('address_key', '')}" if effect.get("address_key") else "",
            f"register={effect.get('register', '')}" if effect.get("register") else "",
            f"value=0x{value_hex}" if value_hex else "",
            f"value_source={effect.get('value_source', '')}" if effect.get("value_source") else "",
            f"category={effect.get('category', '')}" if effect.get("category") else "",
            f"hardware_model={effect.get('hardware_model', '')}" if effect.get("hardware_model") else "",
            f"transfer_model={effect.get('transfer_model', '')}" if effect.get("transfer_model") else "",
            f"transfer_blocked_reason={effect.get('transfer_blocked_reason', '')}"
            if effect.get("transfer_blocked_reason")
            else "",
            f"proof_status={effect.get('proof_status', '')}" if effect.get("proof_status") else "",
            f"hardware_proof_gate={effect.get('hardware_proof_gate', '')}" if effect.get("hardware_proof_gate") else "",
            f"proof_downgrade_reason={effect.get('proof_downgrade_reason', '')}" if effect.get("proof_downgrade_reason") else "",
            f"evidence_source={effect.get('evidence_source', '')}" if effect.get("evidence_source") else "",
            f"evidence_status={effect.get('evidence_status', '')}" if effect.get("evidence_status") else "",
            f"pre_state_sample={effect.get('pre_state_sample', '')}" if effect.get("pre_state_sample") else "",
            f"pre_state_value=0x{effect.get('pre_state_value_hex', '')}" if effect.get("pre_state_value_hex") else "",
            f"pre_state_proof={effect.get('pre_state_proof_status', '')}" if effect.get("pre_state_proof_status") else "",
            f"pre_state_validation={effect.get('pre_state_validation', '')}" if effect.get("pre_state_validation") else "",
            f"pre_state_validation_source={effect.get('pre_state_validation_source', '')}" if effect.get("pre_state_validation_source") else "",
            f"post_value_status={effect.get('post_value_status', '')}" if effect.get("post_value_status") else "",
            f"post_value=0x{effect.get('post_value_hex', '')}" if effect.get("post_value_hex") else "",
            f"post_register_status={effect.get('post_register_status', '')}" if effect.get("post_register_status") else "",
            f"post_register=0x{effect.get('post_register_hex', '')}" if effect.get("post_register_hex") else "",
            f"mode={effect.get('mode', '')}" if effect.get("mode") else "",
            f"source_range={effect.get('source_range', '')}" if effect.get("source_range") else "",
            f"target_range={effect.get('target_range', '')}" if effect.get("target_range") else "",
            f"kind={effect.get('kind', '')}" if effect.get("kind") else "",
            f"missing_registers={','.join(string_items(effect.get('missing_registers')))}" if effect.get("missing_registers") else "",
            f"address_source={effect.get('address_source', '')}" if effect.get("address_source") else "",
            *[
                f"source={render_source_operand(operand)}"
                for operand in dict_items(effect.get("source_operands"))
            ],
        ]
    )


def post_value_label(effect: dict[str, Any]) -> str:
    status = str(effect.get("post_value_status") or "observed")
    address = str(effect.get("address_hex") or effect.get("address") or "")
    return f"post-value {status} {address}".strip()


def post_value_evidence(effect: dict[str, Any], event: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"seq={event.get('seq')}",
            f"pc={event.get('pc_bank_address', '')}",
            f"operation={effect.get('operation', '')}",
            f"address={effect.get('address_hex') or effect.get('address') or ''}",
            f"modeled=0x{effect.get('value_hex', '')}" if effect.get("value_hex") else "",
            f"observed_next=0x{effect.get('post_value_hex', '')}" if effect.get("post_value_hex") else "",
            f"post_value_status={effect.get('post_value_status', '')}" if effect.get("post_value_status") else "",
            f"post_value_source={effect.get('post_value_source', '')}" if effect.get("post_value_source") else "",
            f"post_observed_seq={effect.get('post_observed_seq', '')}" if effect.get("post_observed_seq") not in {None, ""} else "",
            f"post_observed_pc={effect.get('post_observed_pc', '')}" if effect.get("post_observed_pc") else "",
        ]
    )


def post_register_label(effect: dict[str, Any]) -> str:
    status = str(effect.get("post_register_status") or "observed")
    register = str(effect.get("register") or "<register>")
    return f"post-register {status} {register}".strip()


def post_register_evidence(effect: dict[str, Any], event: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"seq={event.get('seq')}",
            f"pc={event.get('pc_bank_address', '')}",
            f"operation={effect.get('operation', '')}",
            f"register={effect.get('register', '')}",
            f"modeled=0x{effect.get('value_hex', '')}" if effect.get("value_hex") else "",
            f"observed_next=0x{effect.get('post_register_hex', '')}" if effect.get("post_register_hex") else "",
            f"post_register_status={effect.get('post_register_status', '')}" if effect.get("post_register_status") else "",
            f"post_register_source={effect.get('post_register_source', '')}" if effect.get("post_register_source") else "",
            f"post_observed_seq={effect.get('post_observed_seq', '')}" if effect.get("post_observed_seq") not in {None, ""} else "",
            f"post_observed_pc={effect.get('post_observed_pc', '')}" if effect.get("post_observed_pc") else "",
        ]
    )


def effect_event_evidence(effect: dict[str, Any], event: dict[str, Any]) -> list[str]:
    base = effect_evidence(effect)
    pre_state = pre_register_evidence(event.get("pre_registers") if event else effect.get("pre_registers"))
    observed = observed_memory_evidence(event.get("observed_memory") if event else effect.get("observed_memory"))
    if not observed:
        return unique_list([*base, *pre_state])
    return unique_list(
        [
            *base[:1],
            *pre_state,
            *observed,
            *base[1:],
        ]
    )


def pre_register_evidence(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return [
        f"pre_{name}={value.get(name)}"
        for name in ("A", "F", "HL", "SP")
        if value.get(name) not in {None, ""}
    ]


def observed_memory_evidence(value: Any) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    out = []
    for item in value[:4]:
        if not isinstance(item, dict):
            continue
        address = str(item.get("address", ""))
        value_hex = str(item.get("value_hex", ""))
        if address and value_hex:
            out.append(f"observed_memory={address}:0x{value_hex}")
    return out


def effect_address_label(effect: dict[str, Any]) -> str:
    address = str(effect.get("address_hex") or effect.get("address") or "")
    key = str(effect.get("address_key") or "")
    if effect.get("bank") is not None and key:
        return key
    return address or key


def effect_related_addresses(effect: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            str(effect.get("address_hex") or effect.get("address") or ""),
            str(effect.get("address_key") or ""),
        ]
    )


def effect_item_proof_status(effect: dict[str, Any]) -> str:
    explicit = normalize_proof_status(effect.get("proof_status")) if effect.get("proof_status") else ""
    if explicit:
        return explicit
    if effect.get("hardware_event_required") and not effect.get("hardware_runtime_event"):
        return "planned_only"
    if str(effect.get("hardware_proof_gate") or "") == "explicit_runtime_event_missing":
        return "planned_only"
    return "instruction_observed"


def watch_hit_proof_status(hit: dict[str, Any]) -> str:
    explicit = normalize_proof_status(hit.get("proof_status")) if hit.get("proof_status") else ""
    if explicit:
        return explicit
    target_match = normalize_proof_status(hit.get("target_match_proof_status")) if hit.get("target_match_proof_status") else ""
    if target_match:
        return target_match
    if str(hit.get("bank_match") or "") in {"bus_address_unverified_bank", "ambiguous_runtime_bank"}:
        return "planned_only"
    return "instruction_observed"


def source_operand_node_id(operand: dict[str, Any]) -> str:
    if operand.get("origin"):
        return node_id("source", operand.get("origin"))
    if operand.get("symbol"):
        return node_id("symbol", operand.get("symbol"))
    if operand.get("kind") == "register":
        return node_id("register", operand.get("name"))
    if operand.get("kind") == "memory":
        if operand.get("address_key"):
            return node_id("address", operand.get("address_key"))
        return node_id("address", operand.get("address"))
    return node_id("operand", source_operand_label(operand))


def source_operand_label(operand: dict[str, Any]) -> str:
    if operand.get("origin"):
        return str(operand.get("origin"))
    if operand.get("symbol"):
        return str(operand.get("symbol"))
    if operand.get("kind") == "register":
        return f"register:{operand.get('name')}"
    if operand.get("kind") == "memory":
        if operand.get("address_key"):
            return str(operand.get("address_key"))
        return str(operand.get("address"))
    if operand.get("kind") == "immediate":
        return f"immediate:{operand.get('value')}"
    return str(operand.get("kind") or "operand")


def source_operand_evidence(operand: dict[str, Any]) -> list[str]:
    provenance = operand.get("register_provenance") if isinstance(operand.get("register_provenance"), dict) else {}
    return unique_list(
        [
            f"kind={operand.get('kind', '')}",
            f"name={operand.get('name', '')}",
            f"value=0x{operand.get('value', '')}" if operand.get("value") else "",
            f"value_source={operand.get('value_source', '')}" if operand.get("value_source") else "",
            f"address={operand.get('address', '')}",
            f"address_key={operand.get('address_key', '')}",
            f"bank={operand.get('bank', '')}",
            f"bank_source={operand.get('bank_source', '')}",
            f"sram_enabled={operand.get('sram_enabled', '')}",
            f"sram_enabled_source={operand.get('sram_enabled_source', '')}",
            f"symbol={operand.get('symbol', '')}",
            f"origin={operand.get('origin', '')}",
            f"via_register={operand.get('via_register', '')}" if operand.get("via_register") else "",
            f"via_register_write_seq={operand.get('via_register_write_seq', '')}" if operand.get("via_register_write_seq") is not None else "",
            f"register_provenance={provenance.get('register', '')}@{provenance.get('pc', '')}" if provenance else "",
        ]
    )


def register_provenance_for_operand(operand: dict[str, Any], attribution: dict[str, Any]) -> dict[str, Any]:
    register = str(operand.get("via_register") or "")
    operand_seq = str(operand.get("via_register_write_seq", ""))
    for provenance in dict_items(attribution.get("register_provenance")):
        if str(provenance.get("register", "")) == register and str(provenance.get("seq", "")) == operand_seq:
            return provenance
    return {
        "register": register,
        "source": str(attribution.get("source") or ""),
        "seq": operand.get("via_register_write_seq"),
        "pc": str(operand.get("via_register_write_pc") or ""),
        "pc_label": "",
        "operation": "",
        "proof_status": normalize_proof_status(attribution.get("proof_status")),
    }


def dynamic_taint_edge_proof_status(proof_status: str, *, has_taint: bool) -> str:
    proof = normalize_proof_status(proof_status)
    if has_taint and proof in {"runtime_observed", "instruction_observed", "taint_proven"}:
        return "taint_proven"
    return proof


def reverse_query_result_proof_status(result: dict[str, Any]) -> str:
    explicit = normalize_proof_status(result.get("proof_status")) if result.get("proof_status") else ""
    if explicit:
        return explicit
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    validation_proof = normalize_proof_status(validation.get("proof_status")) if validation.get("proof_status") else ""
    if validation_proof:
        return validation_proof
    return "instruction_observed" if concrete_reverse_last_writer(result) else "planned_only"


def concrete_reverse_last_writer(result: dict[str, Any]) -> bool:
    last_writer = result.get("last_writer") if isinstance(result.get("last_writer"), dict) else {}
    if not last_writer:
        return False
    seq = last_writer.get("seq", result.get("last_writer_seq"))
    if seq is None or str(seq) == "":
        return False
    pc = str(last_writer.get("pc_label") or last_writer.get("pc") or result.get("last_writer_pc") or "")
    address = str(last_writer.get("address") or last_writer.get("address_key") or result.get("matched_address") or "")
    if not pc or not address:
        return False
    access = str(last_writer.get("access") or "").lower()
    kind = str(last_writer.get("kind") or "").lower()
    if access and "write" not in access:
        return False
    if kind and "write" not in kind and "dma" not in kind and "reset" not in kind:
        return False
    return True


def register_provenance_node_id(provenance: dict[str, Any]) -> str:
    return node_id(
        "register_provenance",
        ":".join(
            [
                str(provenance.get("register") or "register"),
                str(provenance.get("source") or ""),
                str(provenance.get("seq") or ""),
                str(provenance.get("pc") or ""),
            ]
        ),
    )


def register_provenance_label(provenance: dict[str, Any]) -> str:
    register = str(provenance.get("register") or "register")
    pc_label = str(provenance.get("pc_label") or provenance.get("pc") or "")
    operation = str(provenance.get("operation") or "register write")
    return f"{register} <= {operation} at {pc_label}" if pc_label else f"{register} <= {operation}"


def register_provenance_evidence(provenance: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"register={provenance.get('register', '')}",
            f"seq={provenance.get('seq', '')}" if provenance.get("seq") is not None else "",
            f"pc={provenance.get('pc', '')}",
            f"pc_label={provenance.get('pc_label', '')}",
            f"operation={provenance.get('operation', '')}",
            f"value=0x{provenance.get('value_hex', '')}" if provenance.get("value_hex") else "",
            f"value_source={provenance.get('value_source', '')}" if provenance.get("value_source") else "",
            *[f"taint={taint}" for taint in string_items(provenance.get("taint"))],
        ]
    )


def render_source_operand(operand: dict[str, Any]) -> str:
    kind = str(operand.get("kind") or "operand")
    if kind == "register":
        label = f"register:{operand.get('name', '')}"
    elif kind == "memory":
        label = f"memory:{operand.get('address', '')}"
    elif kind == "immediate":
        label = f"immediate:{operand.get('value', '')}"
    else:
        label = kind
    value = str(operand.get("value", ""))
    if value:
        label += f"=0x{value}"
    value_source = str(operand.get("value_source", ""))
    if value_source:
        label += f" value_source={value_source}"
    address_key = str(operand.get("address_key", ""))
    if address_key:
        label += f" key={address_key}"
    bank = str(operand.get("bank", ""))
    if bank:
        label += f" bank={bank}"
    bank_source = str(operand.get("bank_source", ""))
    if bank_source:
        label += f" bank_source={bank_source}"
    if operand.get("sram_enabled") is not None:
        label += f" sram_enabled={operand.get('sram_enabled')}"
    sram_enabled_source = str(operand.get("sram_enabled_source", ""))
    if sram_enabled_source:
        label += f" sram_enabled_source={sram_enabled_source}"
    origin = str(operand.get("origin", ""))
    if origin:
        label += f" origin={origin}"
    symbol = str(operand.get("symbol", ""))
    if symbol and symbol != origin:
        label += f" symbol={symbol}"
    return label


def playtest_packet_symbols(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(data.get("symbols_to_investigate")),
            *string_items(data.get("watch_symbols")),
        ]
    )


def playtest_packet_evidence(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"packet_id={data.get('packet_id', '')}",
            f"artifacts={data.get('artifact_count', 0)}",
            f"routes={data.get('evidence_route_count', 0)}",
            f"save_state={data.get('save_state', '')}",
            f"input_log={data.get('input_log', '')}",
            f"screenshot={data.get('screenshot', '')}",
            *string_items(data.get("warnings"))[:4],
            *string_items(data.get("notes"))[:4],
        ]
    )


def playtest_route_evidence(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"phase={route.get('phase', '')}",
            f"status={route.get('status', '')}",
            f"proof={route.get('proof_status', '')}",
            f"expected_proof={route.get('expected_proof_status', '')}",
            f"produces={route.get('produces', '')}",
            f"runnable={route.get('runnable')}",
            str(route.get("command", "")),
        ]
    )


def visual_snapshot_evidence(data: dict[str, Any]) -> list[str]:
    lcd = data.get("lcd_state") if isinstance(data.get("lcd_state"), dict) else {}
    runtime_samples = visual_snapshot_has_runtime_samples(data)
    return unique_list(
        [
            f"executed={data.get('executed')}",
            f"runtime_samples={runtime_samples}",
            f"surfaces={data.get('surface_count', 0)}",
            f"screen_frames={data.get('screen_frame_count', 0)}",
            f"framebuffer={data.get('framebuffer', '')}" if data.get("framebuffer") else "",
            f"save_state={data.get('save_state', '')}",
            f"lcd_enabled={lcd.get('lcd_enabled', '')}",
            f"ppu_mode={lcd.get('ppu_mode', '')}",
            snapshot_proof_downgrade_evidence(
                data,
                runtime_samples=runtime_samples,
                downgrade_reason="no_visual_runtime_samples",
            ),
        ]
    )


def visual_framebuffer_evidence(frame: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"source={frame.get('screen_source', '')}",
            f"size={frame.get('width', 0)}x{frame.get('height', 0)}",
            f"mode={frame.get('mode', '')}",
            f"bytes={frame.get('byte_count', 0)}",
            f"sha256={frame.get('sha256', '')}",
        ]
    )


def visual_surface_evidence(surface: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"address={surface.get('address', '')}",
            f"bank={surface.get('bank', '')}",
            f"size={surface.get('size', '')}",
            f"nonzero={surface.get('nonzero_count', '')}",
            f"sha256={surface.get('sha256', '')}",
        ]
    )


def audio_snapshot_evidence(data: dict[str, Any]) -> list[str]:
    state = data.get("audio_state") if isinstance(data.get("audio_state"), dict) else {}
    sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
    runtime_samples = audio_snapshot_has_runtime_samples(data)
    return unique_list(
        [
            f"executed={data.get('executed')}",
            f"runtime_samples={runtime_samples}",
            f"registers={data.get('register_count', 0)}",
            f"symbols={data.get('symbol_state_count', 0)}",
            f"sound_buffer={sound_buffer.get('source', '')}" if sound_buffer else "",
            f"sound_buffer_sha256={sound_buffer.get('sha256', '')}" if sound_buffer else "",
            f"save_state={data.get('save_state', '')}",
            f"audio_enabled={state.get('audio_enabled', '')}",
            f"channel_mask={state.get('channel_enable_mask', '')}",
            snapshot_proof_downgrade_evidence(
                data,
                runtime_samples=runtime_samples,
                downgrade_reason="no_audio_runtime_samples",
            ),
        ]
    )


def visual_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    screen_frame = data.get("screen_frame") if isinstance(data.get("screen_frame"), dict) else {}
    io_registers = data.get("io_registers") if isinstance(data.get("io_registers"), dict) else {}
    return bool(
        dict_items(data.get("surfaces"))
        or io_registers
        or screen_frame
        or data.get("framebuffer")
        or positive_int(data.get("screen_frame_count"))
    )


def audio_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    registers = data.get("registers") if isinstance(data.get("registers"), dict) else {}
    wave = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
    sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
    return bool(
        registers
        or dict_items(data.get("register_details"))
        or dict_items(data.get("symbol_state"))
        or wave.get("sha256")
        or wave.get("sample_hex")
        or sound_buffer.get("sha256")
        or sound_buffer.get("sample_hex")
        or sound_buffer.get("buffer")
    )


def snapshot_report_proof_status(
    data: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if runtime_samples:
        return explicit or ("runtime_observed" if data.get("executed") else "planned_only")
    if snapshot_proof_downgrade_evidence(
        data,
        runtime_samples=runtime_samples,
        downgrade_reason=downgrade_reason,
    ):
        return "planned_only"
    return explicit or "planned_only"


def snapshot_proof_downgrade_evidence(
    data: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if runtime_samples:
        return ""
    if bool(data.get("executed")) or explicit in {
        "runtime_observed",
        "instruction_observed",
        "taint_proven",
        "mirror_passed",
        "mirror_failed",
    }:
        return f"proof_downgrade_reason={downgrade_reason}"
    return ""


def audio_register_evidence(register: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"address={register.get('address', '')}",
            f"value={register.get('value_hex', '')}",
        ]
    )


def audio_symbol_state_evidence(item: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"address={item.get('address', '')}",
            f"bank={item.get('bank', '')}",
            f"value={item.get('value_hex', '')}",
            f"bank_read={item.get('bank_read', '')}",
        ]
    )


def audio_wave_ram_evidence(wave: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"address={wave.get('address', '')}",
            f"size={wave.get('size', '')}",
            f"nonzero={wave.get('nonzero_count', '')}",
            f"sha256={wave.get('sha256', '')}",
        ]
    )


def audio_sound_buffer_evidence(sound_buffer: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"source={sound_buffer.get('source', '')}",
            f"sample_rate={sound_buffer.get('sample_rate', '')}",
            f"raw_buffer_head={sound_buffer.get('raw_buffer_head', '')}",
            f"byte_count={sound_buffer.get('byte_count', '')}",
            f"sha256={sound_buffer.get('sha256', '')}",
        ]
    )


def validation_route_evidence(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"phase={route.get('phase', '')}",
            f"status={route.get('status', '')}",
            f"proof={route.get('proof_status', '')}",
            f"expected_proof={route.get('expected_proof_status', '')}",
            f"produces={route.get('produces', '')}",
            f"runnable={route.get('runnable')}",
            str(route.get("command", "")),
        ]
    )


def trace_checkpoint_evidence(checkpoint: dict[str, Any]) -> list[str]:
    data = checkpoint.get("checkpoint") if isinstance(checkpoint.get("checkpoint"), dict) else {}
    span = checkpoint.get("replay_span") if isinstance(checkpoint.get("replay_span"), dict) else {}
    return unique_list(
        [
            f"status={checkpoint.get('status', '')}",
            f"source={data.get('source', '')}",
            f"checkpoint_seq={data.get('seq', '')}",
            f"checkpoint_pc={data.get('pc', '')}",
            f"writer_seq={checkpoint.get('last_writer_seq', '')}",
            f"span={span.get('from_seq', '')}->{span.get('to_seq', '')}",
        ]
    )


def bounded_effect_span_evidence(span: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"status={span.get('status', '')}",
            f"consistent={span.get('consistent')}",
            f"validation_kind={span.get('validation_kind', '')}",
            f"source={span.get('trace_source', '')}",
            f"span={span.get('from_seq', '')}->{span.get('to_seq', '')}",
            f"writes={span.get('write_count', '')}",
            f"final={span.get('final_value_hex', '')}",
            f"expected={span.get('expected_value_hex', '')}",
        ]
    )


def is_boss_ai_report(data: dict[str, Any]) -> bool:
    source = str(data.get("source", ""))
    if source in {
        "trace_rom_pyboy_hooks",
        "python_scenario",
        "python_scenario_contributions",
    }:
        return True
    event_types = {
        str(event.get("event_type", ""))
        for event in dict_items(data.get("events"))
    }
    return bool(event_types & {"score_delta", "score_rule", "policy_check"}) and (
        data.get("scenario_id") is not None or data.get("trace_id") is not None
    )


def boss_ai_proof_status(data: dict[str, Any]) -> str:
    explicit = normalize_proof_status(data.get("proof_status"))
    if data.get("proof_status"):
        return explicit
    if str(data.get("source", "")) == "trace_rom_pyboy_hooks":
        return "runtime_observed"
    return "planned_only"


def boss_ai_trace_kind(data: dict[str, Any]) -> str:
    source = str(data.get("source", ""))
    if source == "trace_rom_pyboy_hooks":
        return "boss_ai_rom_contribution_trace"
    if source == "python_scenario":
        return "boss_ai_decision_trace"
    if source == "python_scenario_contributions":
        return "boss_ai_python_contribution_trace"
    return "boss_ai_trace"


def boss_ai_trace_node_id(data: dict[str, Any], *, source: str, index: int) -> str:
    trace_id = str(data.get("trace_id") or data.get("scenario_id") or data.get("save_state") or source)
    return node_id("boss_ai_trace", f"{source}:{index}:{trace_id}")


def boss_ai_trace_label(data: dict[str, Any], *, fallback: str) -> str:
    scenario_id = str(data.get("scenario_id") or data.get("trace_id") or "")
    if scenario_id:
        return f"Boss AI {scenario_id}"
    save_state = str(data.get("save_state") or "")
    if save_state:
        return f"Boss AI ROM trace {save_state}"
    return f"Boss AI {fallback}"


def boss_ai_report_evidence(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"source={data.get('source', '')}",
            f"scenario={data.get('scenario_id', '')}",
            f"trace={data.get('trace_id', '')}",
            f"save_state={data.get('save_state', '')}",
            f"events={data.get('event_count', '')}",
            f"changed={data.get('changed_event_count', '')}",
            f"rules={data.get('rule_entry_count', data.get('covered_rule_count', ''))}",
            f"predicate_branches={data.get('predicate_branch_entry_count', '')}",
            f"public_read_probes={data.get('public_read_probe_entry_count', '')}",
        ]
    )


def decision_score_event(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else {}
    rule = str(attrs.get("rule_id") or attrs.get("rule") or "")
    return {
        "index": event.get("index"),
        "event_type": "score_delta",
        "operation": "python_score_rule",
        "delta": attrs.get("delta"),
        "changed": attrs.get("delta") not in {None, 0},
        "score_before": attrs.get("before"),
        "score_after": attrs.get("after"),
        "candidate": candidate_from_decision_event(event),
        "source": {
            "rule_id": rule,
            "python_rule": rule,
            "source": str(attrs.get("source", "python_decision_trace")),
            "note": str(attrs.get("note", "")),
        },
    }


def candidate_from_decision_event(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
    slot = attrs.get("slot", "")
    return {
        "kind": "move",
        "slot": slot,
        "slot_index": int(slot) - 1 if str(slot).isdigit() else attrs.get("slot_index", ""),
        "action_id": str(attrs.get("candidate_id", "")),
        "move_name": str(attrs.get("candidate_name") or attrs.get("candidate_id") or ""),
        "initial_score": attrs.get("initial_score"),
        "pre_lookahead_score": attrs.get("pre_lookahead_score"),
        "final_score": attrs.get("final_score"),
        "blocked": attrs.get("blocked"),
    }


def source_info_from_event(event: dict[str, Any]) -> dict[str, Any]:
    source_info = event.get("source")
    return source_info if isinstance(source_info, dict) else {}


def boss_ai_rule_id(source_info: dict[str, Any], event: dict[str, Any]) -> str:
    return str(
        event.get("rule_id")
        or source_info.get("rule_id")
        or source_info.get("python_rule")
        or source_info.get("full_symbol")
        or ""
    )


def boss_ai_candidate_key(candidate: dict[str, Any]) -> str:
    return ":".join(
        part
        for part in [
            str(candidate.get("kind", "")),
            str(candidate.get("action_id") or candidate.get("move_id") or candidate.get("move_name") or ""),
            str(candidate.get("slot") or candidate.get("slot_index") or candidate.get("score_pointer") or ""),
        ]
        if part
    ) or "candidate"


def boss_ai_candidate_label(candidate: dict[str, Any]) -> str:
    name = str(candidate.get("move_name") or candidate.get("action_id") or candidate.get("move_id") or "candidate")
    slot = str(candidate.get("slot") or candidate.get("slot_index") or "")
    return f"{name} slot {slot}" if slot else name


def boss_ai_candidate_evidence(candidate: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"kind={candidate.get('kind', '')}",
            f"slot={candidate.get('slot', '')}",
            f"slot_index={candidate.get('slot_index', '')}",
            f"move_id={candidate.get('move_id', '')}",
            f"action_id={candidate.get('action_id', '')}",
            f"score_pointer={candidate.get('score_pointer', '')}",
            f"initial={candidate.get('initial_score', '')}",
            f"pre_lookahead={candidate.get('pre_lookahead_score', '')}",
            f"final={candidate.get('final_score', '')}",
            f"blocked={candidate.get('blocked', '')}",
        ]
    )


def boss_ai_score_delta_label(event: dict[str, Any], rule_id: str) -> str:
    before = str(event.get("score_before", ""))
    after = str(event.get("score_after", ""))
    delta = str(event.get("delta", ""))
    rule = rule_id or str(event.get("operation") or "score_delta")
    return f"{rule} {before}->{after} delta={delta}"


def boss_ai_score_delta_evidence(event: dict[str, Any]) -> list[str]:
    source_info = source_info_from_event(event)
    return unique_list(
        [
            f"operation={event.get('operation', '')}",
            f"delta={event.get('delta', '')}",
            f"before={event.get('score_before', '')}",
            f"after={event.get('score_after', '')}",
            f"changed={event.get('changed', '')}",
            f"helper={event.get('helper_symbol', '')}",
            f"score_pointer={event.get('score_pointer', '')}",
            f"rule={boss_ai_rule_id(source_info, event)}",
            f"source_label={source_info.get('source_label', '')}",
            f"classification={source_info.get('classification', '')}",
            f"callsite={source_info.get('callsite_symbol', '')}",
            f"note={source_info.get('note', '')}",
        ]
    )


def boss_ai_source_evidence(source_info: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"rule={source_info.get('rule_id', '') or source_info.get('python_rule', '')}",
            f"source_label={source_info.get('source_label', '')}",
            f"full_symbol={source_info.get('full_symbol', '')}",
            f"classification={source_info.get('classification', '')}",
            f"branch_symbol={source_info.get('branch_symbol', '')}",
            f"probe_symbol={source_info.get('probe_symbol', '')}",
            f"hook={source_info.get('hook_bank', '')}:{source_info.get('hook_address', '')}",
            *[f"public_read={item}" for item in string_items(source_info.get("public_reads"))],
        ]
    )


def boss_ai_branch_evidence(event: dict[str, Any]) -> list[str]:
    source_info = source_info_from_event(event)
    return unique_list(
        [
            f"predicate={event.get('predicate_id', '')}",
            f"outcome={event.get('outcome', '')}",
            *boss_ai_source_evidence(source_info),
        ]
    )


def boss_ai_probe_evidence(event: dict[str, Any]) -> list[str]:
    source_info = source_info_from_event(event)
    snapshot = event.get("snapshot") if isinstance(event.get("snapshot"), dict) else {}
    return unique_list(
        [
            f"probe={event.get('probe_id', '')}",
            f"outcome={event.get('outcome', '')}",
            *[f"snapshot={key}" for key in snapshot.keys()],
            *boss_ai_source_evidence(source_info),
        ]
    )


def boss_ai_selector_evidence(selector: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"ready={selector.get('ready', '')}",
            f"best={selector.get('best_action_id', '')}",
            f"second={selector.get('second_action_id', '')}",
            f"best_score={selector.get('best_score', '')}",
            f"second_score={selector.get('second_score', '')}",
            f"gap={selector.get('gap', '')}",
            f"threshold={selector.get('best_roll_threshold', '')}",
        ]
    )


def boss_ai_policy_evidence(policy: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"verdict={policy.get('verdict', '')}",
            f"severity={policy.get('severity', '')}",
            f"reason={policy.get('reason', '')}",
            *[f"expected_best={item}" for item in string_items(policy.get("expected_best_action_ids"))],
            *[f"rolled_bad={item}" for item in string_items(policy.get("rolled_bad_action_ids"))],
        ]
    )


def target_node_id(value: Any) -> str:
    text = str(value or "")
    return node_id(target_kind(text), text)


def target_kind(value: Any) -> str:
    text = str(value or "").strip()
    if looks_like_address(text):
        return "address"
    if text.startswith("register:"):
        return "register"
    return "symbol"


def symbol_if_not_address(value: Any) -> str:
    text = str(value or "").strip()
    return "" if looks_like_address(text) else text


def looks_like_address(value: str) -> bool:
    text = str(value).strip()
    if not text:
        return False
    if text.startswith("$") or ":" in text:
        return True
    if len(text) == 4 and all(char in "0123456789abcdefABCDEF" for char in text):
        return True
    return False


def node_id(kind: str, value: Any) -> str:
    return f"{safe_id(kind)}:{safe_id(value)}"


def safe_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "unknown"
    return "".join(char if char.isalnum() or char in {"_", "-", ".", ":"} else "_" for char in text)[:180]


def normalize_proof_status(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "planned": "planned_only",
        "planning": "planned_only",
        "runtime": "runtime_observed",
        "observed": "runtime_observed",
        "instruction": "instruction_observed",
        "taint": "taint_proven",
    }
    text = aliases.get(text, text)
    return text if text in PROOF_STATUSES else "planned_only"


def strongest_proof_status(values: Any) -> str:
    statuses = [normalize_proof_status(value) for value in values]
    return max(statuses or ["planned_only"], key=lambda status: PROOF_STATUS_ORDER.get(status, 0))


def weakest_proof_status(values: Any) -> str:
    statuses = [normalize_proof_status(value) for value in values]
    return min(statuses or ["planned_only"], key=lambda status: PROOF_STATUS_ORDER.get(status, 0))


def proof_summary(values: Any) -> dict[str, Any]:
    statuses = [normalize_proof_status(value) for value in values]
    return {
        "max": strongest_proof_status(statuses),
        "min": weakest_proof_status(statuses),
        "source_count": len(statuses),
    }


def proof_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = normalize_proof_status(item.get("proof_status"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [nested for item in value for nested in string_items(item)]
    if isinstance(value, dict):
        return [nested for item in value.values() for nested in string_items(item)]
    return [str(value)] if value else []


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
