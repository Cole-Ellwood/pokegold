"""Re-derive counterfactual witnesses from old-basis artifacts by re-execution.

Old witness artifacts embed their full recipe (save_state + memory_patches +
mutation). This driver re-runs each unique context on the CURRENT trace ROM via
the materializer's own session and credits only flips that the current universe
inventory still needs. No restamping: a context that no longer flips is skipped
and counted.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from tools.boss_ai_debugger.rom_contribution_trace import (
    MemoryPatch,
    RomContributionTraceSession,
)
from tools.boss_ai_debugger.rom_counterfactual_materialize import (
    COUNTERFACTUAL_MATERIALIZATION_KIND,
    COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE,
    GENERATOR_ID,
    SCHEMA_VERSION,
    counterfactual_mutation_changed_key,
    counterfactual_witnesses_for_traces,
    move_choice_observable,
    stamp_trace,
    switch_dispatch_observable,
)
from tools.boss_ai_debugger.universe import (
    ALLOWED_COUNTERFACTUAL_MUTATION_KEYS,
    COUNTERFACTUAL_MUTATION_ALLOWLIST,
    build_boss_ai_universe_report,
)

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "audit/boss_ai_debugger/god_level_benchmark/artifacts/counterfactual_witness_materializations"
ROM = ROOT / "pokegold_trace.gbc"
SYMBOLS = ROOT / "pokegold_trace.sym"
MAX_CONTEXTS = 70
UNIVERSE_REFRESH_EVERY = 8

log_path = ROOT / ".local" / "tmp" / "witness_reexec.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_file = open(log_path, "w", encoding="utf-8")


def note(msg: str) -> None:
    print(msg, flush=True)
    log_file.write(msg + "\n")
    log_file.flush()


def patches_from(rows: list[dict]) -> list[MemoryPatch] | None:
    out = []
    for row in rows or []:
        try:
            out.append(
                MemoryPatch(
                    symbol_name=str(row["symbol_name"]),
                    offset=int(row.get("offset", 0)),
                    value=int(row["value"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            return None
    return out


def missing_rules(universe: dict) -> set[str]:
    rows = (universe.get("exhaustive_class_witness_catalog") or {}).get("catalog_rows") or []
    return {
        r.get("rule_id", "")
        for r in rows
        if r.get("status") == "cataloged_missing_rom_proof"
    }


def collect_contexts(live_identity: dict) -> list[dict]:
    contexts = []
    seen = set()
    skipped_delayed = 0
    for path in sorted(ART.glob("*.json")):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        basis = artifact.get("basis") or {}
        if basis == live_identity:
            continue  # already current-basis
        for witness in artifact.get("witnesses") or []:
            trace = witness.get("baseline_trace") or {}
            mutation = (witness.get("mutation") or {}).get("patch") or {}
            save_state = str(trace.get("save_state") or "")
            if not save_state or not mutation.get("symbol_name"):
                continue
            if trace.get("delayed_patch_entry_count"):
                skipped_delayed += 1
                continue
            base_patches = patches_from(trace.get("memory_patches") or [])
            mut = patches_from([mutation])
            if base_patches is None or not mut:
                continue
            surface = str(witness.get("decision_surface") or "")
            key = (
                save_state,
                tuple((p.symbol_name, p.offset, p.value) for p in base_patches),
                (mut[0].symbol_name, mut[0].offset, mut[0].value),
                surface,
            )
            if key in seen:
                continue
            seen.add(key)
            contexts.append(
                {
                    "save_state": save_state,
                    "patches": base_patches,
                    "mutation": mut[0],
                    "surface": surface,
                    "rule_id": witness.get("rule_id", ""),
                    "origin": path.name,
                    # Emission filenames key off this, NOT the sort position:
                    # sort order depends on which rules are still missing, so
                    # it changes between runs and would map different contexts
                    # onto the same file.
                    "context_id": hashlib.sha1(repr(key).encode("utf-8")).hexdigest()[:16],
                }
            )
    note(f"contexts: {len(contexts)} unique (skipped {skipped_delayed} delayed-patch witnesses)")
    return contexts


def current_state_by_route() -> dict[str, Path]:
    """Map route prefixes to CURRENT manifest seed states for stale-path remap."""
    manifest = json.loads(
        (ROOT / "audit/boss_ai_trace/live_capture_manifest.json").read_text(encoding="utf-8")
    )
    mapping: dict[str, Path] = {}
    for entry in manifest.get("captures", []):
        if not isinstance(entry, dict):
            continue
        route = str(entry.get("id", "")).lower()
        for field in ("pre_choice_state", "save_state", "score_materialization_state"):
            value = entry.get(field)
            if isinstance(value, str) and value:
                path = Path(value)
                if not path.is_absolute():
                    path = ROOT / path
                if path.exists():
                    mapping.setdefault(f"{route}:{field}", path)
    return mapping


def remap_stale_state(state_path: Path, mapping: dict[str, Path]) -> Path | None:
    """Find the current equivalent of a deleted seed-state path by route+kind."""
    name = state_path.name.lower()
    if name.startswith("route:"):
        route = name.split(":", 1)[1]
        for field in ("pre_choice_state", "save_state"):
            current = mapping.get(f"{route}:{field}")
            if current is not None:
                return current
        return None
    for key, current in mapping.items():
        route, field = key.split(":", 1)
        if not name.startswith(route):
            continue
        if "pre_choice" in name and field == "pre_choice_state":
            return current
        if "score_materialization" in name and field == "score_materialization_state":
            return current
        if "chosen" in name and field == "save_state":
            return current
    # Last resort: any current state for the route prefix.
    for key, current in mapping.items():
        route = key.split(":", 1)[0]
        if name.startswith(route):
            return current
    return None


def merge_prior_witnesses(path: Path, witnesses: list[dict], basis: dict) -> list[dict]:
    """Union new witnesses with an existing same-basis emission for this context.

    A re-run filters witnesses to still-needed rules, so re-emitting the same
    context can legitimately produce a smaller set; replacing the file would
    drop rules whose only credit lives here. A file from a different basis is
    stale (the universe ignores it) and is replaced wholesale.
    """
    if not path.exists():
        return witnesses
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return witnesses
    if existing.get("basis") != basis:
        return witnesses
    merged = list(witnesses)
    have = {(w.get("rule_id", ""), w.get("witness_role", "")) for w in merged}
    for prior in existing.get("witnesses") or []:
        if not isinstance(prior, dict):
            continue
        if (prior.get("rule_id", ""), prior.get("witness_role", "")) in have:
            continue
        merged.append(prior)
    return merged


def main() -> int:
    universe = build_boss_ai_universe_report(rom_path=ROM, symbols_path=SYMBOLS)
    need = missing_rules(universe)
    note(f"missing rules at start: {len(need)}")
    contexts = collect_contexts(universe["class_identity"])
    # Prioritize contexts whose origin witness rule is still missing.
    contexts.sort(key=lambda c: (c["rule_id"] not in need, c["origin"]))
    route_states = current_state_by_route()
    ran = flips = emitted = stale_state = 0
    since_refresh = 0
    for index, ctx in enumerate(contexts[:MAX_CONTEXTS]):
        if not need:
            break
        state_path = Path(ctx["save_state"])
        if not state_path.is_absolute():
            state_path = ROOT / state_path
        if not state_path.exists():
            remapped = remap_stale_state(state_path, route_states)
            if remapped is None:
                stale_state += 1
                continue
            note(f"  remap {state_path.name} -> {remapped.name}")
            state_path = remapped
        mutation = ctx["mutation"]
        mutation_key = counterfactual_mutation_changed_key(mutation)
        if mutation_key not in ALLOWED_COUNTERFACTUAL_MUTATION_KEYS:
            continue
        # Switch-loop predispatch states only materialize on the switch path,
        # regardless of which decision surface the original witness credited.
        is_switch = (
            ctx["surface"] == "switch_dispatch"
            or "switch_loop" in state_path.name.lower()
            or "predispatch" in state_path.name.lower()
        )
        run_kwargs = {
            "save_state": state_path,
            "watch_frames": 240,
            "metadata": {"boss": "reexec", "notes": f"witness-reexec:{ctx['origin']}"},
        }
        if is_switch:
            run_kwargs["button"] = ""
            run_kwargs["finish_on"] = "switch"
        else:
            run_kwargs["button"] = "a"
            run_kwargs["finish_on"] = "choice"
        ran += 1
        started = time.perf_counter()
        try:
            with RomContributionTraceSession(rom=ROM, symbols_path=SYMBOLS) as session:
                baseline = session.run(memory_patches=ctx["patches"], **run_kwargs)
                counterfactual = session.run(
                    memory_patches=[*ctx["patches"], mutation], **run_kwargs
                )
        except Exception as exc:  # noqa: BLE001 - per-context fail-closed skip
            note(f"  context {index} error: {str(exc)[:140]}")
            continue
        observable_fn = switch_dispatch_observable if is_switch else move_choice_observable
        baseline_observable = observable_fn(baseline)
        counterfactual_observable = observable_fn(counterfactual)
        if baseline_observable == counterfactual_observable:
            continue
        flips += 1
        scenario = {"id": f"reexec_{ctx['context_id']}_{ctx['origin']}"}
        stamp_trace(baseline, scenario=scenario, trace_id=f"{scenario['id']}__baseline")
        stamp_trace(
            counterfactual,
            scenario=scenario,
            trace_id=f"{scenario['id']}__{mutation_key}_{mutation.value:02x}",
        )
        if since_refresh >= UNIVERSE_REFRESH_EVERY:
            universe = build_boss_ai_universe_report(rom_path=ROM, symbols_path=SYMBOLS)
            need = missing_rules(universe)
            since_refresh = 0
        witnesses = counterfactual_witnesses_for_traces(
            universe,
            baseline_trace=baseline,
            counterfactual_trace=counterfactual,
            mutation=mutation,
            mutation_key=mutation_key,
            baseline_observable=baseline_observable,
            counterfactual_observable=counterfactual_observable,
            supported_decision_surfaces=frozenset(
                {"switch_dispatch", "boss_ai_rule", "move_score"}
            ),
        )
        since_refresh += 1
        if not witnesses:
            continue
        out = ART / f"reexec_witnesses_{ctx['context_id']}.json"
        witnesses = merge_prior_witnesses(out, witnesses, universe["class_identity"])
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": COUNTERFACTUAL_MATERIALIZATION_KIND,
            "source": f"reexec:{ctx['origin']}",
            "generator": GENERATOR_ID,
            "basis": universe["class_identity"],
            "proof_scope": COUNTERFACTUAL_MATERIALIZATION_PROOF_SCOPE,
            "base_route": "reexec",
            "base_state": str(state_path),
            "scenario_count": 1,
            "checked_count": len(witnesses),
            "skipped_count": 0,
            "error_count": 0,
            "policy_disagreement_count": 0,
            "elapsed_seconds": time.perf_counter() - started,
            "scenario_id": scenario["id"],
            "surface": "switch_dispatch" if is_switch else "move_choice",
            "mutation": {
                "allowlist": COUNTERFACTUAL_MUTATION_ALLOWLIST,
                "changed_keys": [mutation_key],
                "patch": {
                    "symbol_name": mutation.symbol_name,
                    "offset": mutation.offset,
                    "value": mutation.value,
                },
            },
            "baseline_observable": baseline_observable,
            "counterfactual_observable": counterfactual_observable,
            "witnesses": witnesses,
        }
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        emitted += 1
        credited = {w.get("rule_id", "") for w in witnesses}
        need -= credited
        note(
            f"  EMIT {out.name} witnesses={len(witnesses)} "
            f"credited_missing={len(credited & set(need)) + len(credited - need)} remaining~{len(need)}"
        )
    note(
        f"DONE ran={ran} flips={flips} emitted={emitted} stale_state={stale_state} "
        f"remaining_missing~{len(need)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
