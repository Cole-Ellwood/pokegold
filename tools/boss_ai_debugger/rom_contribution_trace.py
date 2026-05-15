from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .rule_map import build_rule_map


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM_CONTRIBUTION_TRACE_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_smoke.json"
)
DEFAULT_ROM_CONTRIBUTION_TRACE_PROBE_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_spikes_spin_probe.json"
)

PARTY_LENGTH = 6
PARTYMON_STRUCT_LENGTH = 48

PUBLIC_INPUT_SNAPSHOT_WIDTHS = {
    "wPlayerScreens": 1,
    "wEnemyScreens": 1,
    "wPlayerUsedMoves": 4,
    "wEnemyMonType1": 1,
    "wEnemyMonType2": 1,
    "wEnemySubStatus1": 1,
    "wOTPartyCount": 1,
    "wOTPartySpecies": PARTY_LENGTH + 1,
    "wBossAITier": 1,
    "wBossAISeenPlayerSpeciesCount": 1,
    "wBossAISeenPlayerSpecies": PARTY_LENGTH,
    "wBossAISeenPlayerAliveMask": 1,
    "wBossAISpeciesUsedMoves": PARTY_LENGTH * 4,
    "wBattleMonSpecies": 1,
    "wBattleMonLevel": 1,
}

STATIC_PUBLIC_TABLE_SYMBOLS = {
    "BaseData": "BaseData",
    "EvosAttacks": "EvosAttacksPointers",
}

SCORE_HELPERS = {
    "BossAI_ApplyMoveModel.EncourageScoreByA": "encourage_tier_weight",
    "BossAI_ApplyMoveModel.DiscourageScoreByA": "discourage_tier_weight",
    "BossAI_SetScoreHL": "set_score",
    "BossAI_EncourageScoreHL": "encourage_score",
    "BossAI_DiscourageScoreHL": "discourage_score",
    "BossAI_ApplySignedDeltaToScore": "apply_signed_lookahead_delta",
}

POINTER_FROM_WRAM_SCORE_PTR = {
    "BossAI_SetScoreHL",
    "BossAI_EncourageScoreHL",
    "BossAI_DiscourageScoreHL",
}

CONTROL_HOOKS = {
    "BossAI_ApplyMoveModel.ScoreMove": "candidate_start",
    "BossAI_ApplyMoveModel.TracePostModelScore": "candidate_end",
}

PREDICATE_BRANCH_HOOKS = {
    "BossAI_ApplyMoveModel.spikes_layer1": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "zero_existing_layers",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_layer2": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "one_existing_layer",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_layer3": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "two_existing_layers",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_l2_no_revealed_spin": {
        "predicate_id": "active_revealed_rapid_spin",
        "outcome": "not_revealed_for_layer2",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerUsedMoves",),
    },
    "BossAI_ApplyMoveModel.spikes_l3_no_revealed_spin": {
        "predicate_id": "active_revealed_rapid_spin",
        "outcome": "not_revealed_for_layer3",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerUsedMoves",),
    },
    "BossAI_ApplyMoveModel.revealed_spin_not_blocked": {
        "predicate_id": "revealed_rapid_spin_active_spinblock",
        "outcome": "not_blocked",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedRapidSpinSpikesRisk",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
        ),
    },
    "BossAI_ApplyMoveModel.revealed_spin_soft": {
        "predicate_id": "revealed_rapid_spin_spikes_risk",
        "outcome": "softened_by_spinblock_context",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedRapidSpinSpikesRisk",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "wEnemySubStatus1",
            "wOTPartySpecies",
            "wOTPartyMon1HP",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l2_soft_spin_risk": {
        "predicate_id": "layer2_unrevealed_spin_risk",
        "outcome": "soft_penalty",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer2UnrevealedSpinRisk",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISpeciesUsedMoves",
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l3_soft_spin_risk": {
        "predicate_id": "layer3_unrevealed_spin_risk",
        "outcome": "active_species_prior_or_late_game",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "wBossAITier",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l3_bench_spin_risk": {
        "predicate_id": "layer3_seen_bench_revealed_spin",
        "outcome": "bench_spinner_seen_alive",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.enemy_not_spinblocking": {
        "predicate_id": "enemy_active_spinblock",
        "outcome": "not_spinblocking",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyActiveBlocksRapidSpin",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
        ),
    },
    "BossAI_ApplyMoveModel.reserve_ghost_yes_pop": {
        "predicate_id": "boss_reserve_spinblock",
        "outcome": "available",
        "parent_symbol": "BossAI_ApplyMoveModel.BossHasAvailableReserveGhost",
        "legal_inputs": (
            "wOTPartySpecies",
            "wOTPartyMon1HP",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.reserve_ghost_no": {
        "predicate_id": "boss_reserve_spinblock",
        "outcome": "unavailable",
        "parent_symbol": "BossAI_ApplyMoveModel.BossHasAvailableReserveGhost",
        "legal_inputs": (
            "wOTPartyCount",
            "wOTPartySpecies",
            "wOTPartyMon1HP",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.bench_spin_yes_pop": {
        "predicate_id": "seen_bench_revealed_rapid_spin",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenBenchRevealedRapidSpin",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.bench_spin_no": {
        "predicate_id": "seen_bench_revealed_rapid_spin",
        "outcome": "not_found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenBenchRevealedRapidSpin",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.active_spin_yes": {
        "predicate_id": "active_species_levelup_rapid_spin_prior",
        "outcome": "can_learn",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerActiveLikelyCanRapidSpin",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.active_spin_no": {
        "predicate_id": "active_species_levelup_rapid_spin_prior",
        "outcome": "cannot_infer",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerActiveLikelyCanRapidSpin",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.species_spin_yes": {
        "predicate_id": "species_levelup_rapid_spin",
        "outcome": "available_by_level",
        "parent_symbol": "BossAI_ApplyMoveModel.SpeciesLevelUpHasRapidSpin",
        "legal_inputs": (
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.species_spin_no": {
        "predicate_id": "species_levelup_rapid_spin",
        "outcome": "not_available_by_level",
        "parent_symbol": "BossAI_ApplyMoveModel.SpeciesLevelUpHasRapidSpin",
        "legal_inputs": (
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
}


@dataclass(frozen=True)
class HookTarget:
    kind: str
    full_symbol: str
    operation: str
    bank: int
    address: int
    predicate_id: str = ""
    outcome: str = ""
    parent_symbol: str = ""
    legal_inputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryPatch:
    symbol_name: str
    offset: int
    value: int


@dataclass(frozen=True)
class RuleFrame:
    sp: int
    full_symbol: str
    rule: dict[str, Any]


@dataclass(frozen=True)
class PendingScore:
    helper_symbol: str
    operation: str
    amount: int
    pointer: int
    before: int
    candidate: dict[str, Any]
    source: dict[str, Any]


class SymbolIndex:
    def __init__(
        self,
        symbols: dict[str, capture.Symbol],
        rule_map: dict[str, Any],
    ) -> None:
        self.symbols = symbols
        self.rule_by_full_symbol = build_rule_lookup(rule_map)
        self.symbols_by_bank: dict[int, list[tuple[int, str]]] = {}
        self.rules_by_bank: dict[int, list[tuple[int, str]]] = {}
        for name, symbol in symbols.items():
            self.symbols_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.symbols_by_bank.values():
            items.sort()
        for name in self.rule_by_full_symbol:
            symbol = symbols.get(name)
            if symbol is None:
                continue
            self.rules_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.rules_by_bank.values():
            items.sort()

    def hook_targets(self) -> list[HookTarget]:
        targets: list[HookTarget] = []
        names: dict[str, tuple[str, str]] = {}
        for name in self.rule_by_full_symbol:
            if not is_executable_hook_label(name):
                continue
            names[name] = ("rule", "")
        for name, operation in SCORE_HELPERS.items():
            names[name] = ("score_helper", operation)
        for name, operation in CONTROL_HOOKS.items():
            names[name] = ("control", operation)

        for name, (kind, operation) in names.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind=kind,
                    full_symbol=name,
                    operation=operation,
                    bank=symbol.bank,
                    address=symbol.address,
                )
            )
        for name, spec in PREDICATE_BRANCH_HOOKS.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind="predicate_branch",
                    full_symbol=name,
                    operation=str(spec["outcome"]),
                    bank=symbol.bank,
                    address=symbol.address,
                    predicate_id=str(spec["predicate_id"]),
                    outcome=str(spec["outcome"]),
                    parent_symbol=str(spec["parent_symbol"]),
                    legal_inputs=tuple(str(item) for item in spec["legal_inputs"]),
                )
            )
        return targets

    def nearest_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.symbols_by_bank.get(bank, []), address)

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.rules_by_bank.get(bank, []), address)

    def rule_for(self, full_symbol: str) -> dict[str, Any] | None:
        return self.rule_by_full_symbol.get(full_symbol)


class RomContributionTracer:
    def __init__(
        self,
        pyboy: Any,
        symbols: dict[str, capture.Symbol],
        symbol_index: SymbolIndex,
        move_names: dict[int, str],
        memory_patches: list[MemoryPatch] | None = None,
    ) -> None:
        self.pyboy = pyboy
        self.symbols = symbols
        self.symbol_index = symbol_index
        self.move_names = move_names
        self.memory_patches = memory_patches or []
        self.score_start_patches_applied = False
        self.frames: list[RuleFrame] = []
        self.pending: PendingScore | None = None
        self.events: list[dict[str, Any]] = []
        self.rule_entries: list[dict[str, Any]] = []
        self.predicate_branch_entries: list[dict[str, Any]] = []

    def reset(self, *, memory_patches: list[MemoryPatch] | None = None) -> None:
        self.memory_patches = memory_patches or []
        self.score_start_patches_applied = False
        self.frames.clear()
        self.pending = None
        self.events.clear()
        self.rule_entries.clear()
        self.predicate_branch_entries.clear()

    def handle_hook(self, targets: list[HookTarget]) -> None:
        for target in sorted(targets, key=hook_order):
            if target.kind == "rule":
                self.handle_rule(target)
            elif target.kind == "score_helper":
                self.handle_score_helper(target)
            elif target.kind == "control":
                self.handle_control(target)
            elif target.kind == "predicate_branch":
                self.handle_predicate_branch(target)

    def handle_rule(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        rule = self.symbol_index.rule_for(target.full_symbol)
        if rule is None:
            return
        frame = RuleFrame(sp=sp, full_symbol=target.full_symbol, rule=rule)
        if self.frames and self.frames[-1].sp == sp:
            self.frames[-1] = frame
        else:
            self.frames.append(frame)
        self.rule_entries.append(
            {
                "index": len(self.rule_entries) + 1,
                "event_type": "rule_enter",
                "sp": f"{sp:04x}",
                "candidate": self.active_score_candidate(),
                "move_struct": self.current_move_struct(),
                "source": self.source_for_rule_entry(target, rule),
            }
        )

    def handle_score_helper(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        pointer = self.score_pointer_for_helper(target)
        before = self.read_addr(pointer)
        amount = int(self.pyboy.register_file.A) & 0xFF
        self.pending = PendingScore(
            helper_symbol=target.full_symbol,
            operation=target.operation,
            amount=amount,
            pointer=pointer,
            before=before,
            candidate=self.candidate_for_score_pointer(pointer),
            source=self.source_for_score_helper(target),
        )

    def handle_predicate_branch(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        self.predicate_branch_entries.append(
            {
                "index": len(self.predicate_branch_entries) + 1,
                "event_type": "predicate_branch",
                "sp": f"{sp:04x}",
                "candidate": self.active_score_candidate(),
                "move_struct": self.current_move_struct(),
                "predicate": {
                    "predicate_id": target.predicate_id,
                    "outcome": target.outcome,
                    "branch_symbol": target.full_symbol,
                    "parent_symbol": target.parent_symbol,
                    "legal_inputs": list(target.legal_inputs),
                },
                "public_input_snapshot": self.public_input_snapshot(
                    target.legal_inputs
                ),
                "source": self.source_for_predicate_branch(target),
            }
        )

    def score_pointer_for_helper(self, target: HookTarget) -> int:
        if target.full_symbol in POINTER_FROM_WRAM_SCORE_PTR:
            symbol = self.symbols["wBossAIScorePtr"]
            high = trace_runtime.read_byte(self.pyboy, symbol)
            low = trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + 1),
            )
            return (high << 8) | low
        return int(self.pyboy.register_file.HL)

    def handle_control(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        if target.operation == "candidate_start":
            if not self.score_start_patches_applied:
                apply_memory_patches(self.pyboy, self.symbols, self.memory_patches)
                self.score_start_patches_applied = True
            self.frames.clear()

    def close_pending(self, *, trigger: str) -> None:
        pending = self.pending
        if pending is None:
            return
        self.pending = None
        after = self.read_addr(pending.pointer)
        delta = after - pending.before
        self.events.append(
            {
                "index": len(self.events) + 1,
                "event_type": "score_delta",
                "helper_symbol": pending.helper_symbol,
                "operation": pending.operation,
                "amount_register_a": pending.amount,
                "score_pointer": f"{pending.pointer:04x}",
                "score_before": pending.before,
                "score_after": after,
                "delta": delta,
                "changed": delta != 0,
                "candidate": pending.candidate,
                "source": pending.source,
                "closed_by": trigger,
            }
        )

    def pop_returned_frames(self, sp: int) -> None:
        while self.frames and self.frames[-1].sp < sp:
            self.frames.pop()

    def active_frame(self) -> RuleFrame | None:
        if not self.frames:
            return None
        return self.frames[-1]

    def source_for_score_helper(self, target: HookTarget) -> dict[str, Any]:
        frame = self.active_frame()
        return_address = self.stack_return_address()
        callsite_symbol = self.symbol_index.nearest_symbol(
            target.bank,
            return_address,
        )
        callsite_rule_symbol = self.symbol_index.nearest_rule_symbol(
            target.bank,
            return_address,
        )
        callsite_rule = self.symbol_index.rule_for(callsite_rule_symbol)
        rule = frame.rule if frame is not None else callsite_rule
        full_symbol = frame.full_symbol if frame is not None else callsite_rule_symbol
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "callsite_symbol": callsite_symbol,
            "callsite_rule_symbol": callsite_rule_symbol,
            "return_address": f"{return_address:04x}",
            "hook_bank": f"{target.bank:02x}",
        }

    def source_for_rule_entry(
        self,
        target: HookTarget,
        rule: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "rule_id": rule.get("rule_id", ""),
            "source_label": rule.get("source_label", ""),
            "full_symbol": target.full_symbol,
            "classification": rule.get("classification", ""),
            "public_reads": rule.get("public_reads", []),
            "static_public_read_hints": rule.get("public_reads", []),
            "hook_bank": f"{target.bank:02x}",
            "hook_address": f"{target.address:04x}",
        }

    def source_for_predicate_branch(self, target: HookTarget) -> dict[str, Any]:
        rule = self.symbol_index.rule_for(target.parent_symbol)
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": target.parent_symbol,
            "branch_symbol": target.full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "dynamic_branch_legal_inputs": list(target.legal_inputs),
            "hook_bank": f"{target.bank:02x}",
            "hook_address": f"{target.address:04x}",
        }

    def active_score_candidate(self) -> dict[str, Any]:
        if "wBossAIScorePtr" not in self.symbols:
            return unknown_candidate()
        try:
            symbol = self.symbols["wBossAIScorePtr"]
            high = trace_runtime.read_byte(self.pyboy, symbol)
            low = trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + 1),
            )
        except Exception:
            return unknown_candidate()
        return self.candidate_for_score_pointer((high << 8) | low)

    def candidate_for_score_pointer(self, pointer: int) -> dict[str, Any]:
        base = self.symbols["wEnemyAIMoveScores"]
        offset = pointer - base.address
        if 0 <= offset < 4:
            move_symbol = self.symbols["wEnemyMonMoves"]
            move_id = self.read_symbol_offset(move_symbol, offset)
            return {
                "kind": "move",
                "slot_index": offset,
                "slot": offset + 1,
                "move_id": move_id,
                "move_name": self.move_names.get(move_id, f"#{move_id:02x}"),
            }
        return {
            **unknown_candidate(),
            "score_pointer": f"{pointer:04x}",
        }

    def current_move_struct(self) -> dict[str, int]:
        symbol_names = {
            "animation": "wEnemyMoveStructAnimation",
            "effect": "wEnemyMoveStructEffect",
            "power": "wEnemyMoveStructPower",
            "type": "wEnemyMoveStructType",
            "accuracy": "wEnemyMoveStructAccuracy",
            "pp": "wEnemyMoveStructPP",
            "effect_chance": "wEnemyMoveStructEffectChance",
        }
        values: dict[str, int] = {}
        for key, name in symbol_names.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            try:
                values[key] = int(trace_runtime.read_byte(self.pyboy, symbol))
            except Exception:
                continue
        return values

    def public_input_snapshot(self, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self.snapshot_public_input(name) for name in names}

    def snapshot_public_input(self, name: str) -> dict[str, Any]:
        if name == "wOTPartyMon1HP":
            return self.party_hp_snapshot(name)

        static_symbol_name = STATIC_PUBLIC_TABLE_SYMBOLS.get(name)
        if static_symbol_name is not None:
            return self.static_table_snapshot(name, static_symbol_name)

        symbol = self.symbols.get(name)
        if symbol is None:
            return {
                "available": False,
                "reason": "symbol not found",
            }
        width = PUBLIC_INPUT_SNAPSHOT_WIDTHS.get(name, 1)
        try:
            values = [
                self.read_symbol_offset(symbol, offset)
                for offset in range(width)
            ]
        except Exception as exc:
            return {
                "available": False,
                "symbol": name,
                "bank": f"{symbol.bank:02x}",
                "address": f"{symbol.address:04x}",
                "width": width,
                "reason": f"read failed: {exc}",
            }
        return {
            "available": True,
            "kind": "byte_range",
            "symbol": name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "width": width,
            "values": values,
        }

    def party_hp_snapshot(self, name: str) -> dict[str, Any]:
        symbol = self.symbols.get(name)
        if symbol is None:
            return {
                "available": False,
                "reason": "symbol not found",
            }
        slots = []
        try:
            for slot_index in range(PARTY_LENGTH):
                address = symbol.address + (slot_index * PARTYMON_STRUCT_LENGTH)
                values = [
                    self.read_symbol_offset(
                        capture.Symbol(symbol.bank, address),
                        offset,
                    )
                    for offset in range(4)
                ]
                slots.append(
                    {
                        "slot_index": slot_index,
                        "address": f"{address:04x}",
                        "values": values,
                    }
                )
        except Exception as exc:
            return {
                "available": False,
                "symbol": name,
                "bank": f"{symbol.bank:02x}",
                "address": f"{symbol.address:04x}",
                "reason": f"read failed: {exc}",
            }
        return {
            "available": True,
            "kind": "party_hp_slots",
            "symbol": name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "slot_count": len(slots),
            "slot_width": 4,
            "stride": PARTYMON_STRUCT_LENGTH,
            "slots": slots,
        }

    def static_table_snapshot(
        self,
        input_name: str,
        symbol_name: str,
    ) -> dict[str, Any]:
        symbol = self.symbols.get(symbol_name)
        if symbol is None:
            return {
                "available": False,
                "kind": "static_table_reference",
                "symbol": symbol_name,
                "reason": "symbol not found",
            }
        return {
            "available": True,
            "kind": "static_table_reference",
            "input": input_name,
            "symbol": symbol_name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "values": [],
            "note": "static ROM table reference; branch-specific table bytes are not sampled",
        }

    def stack_return_address(self) -> int:
        sp = int(self.pyboy.register_file.SP)
        low = int(self.pyboy.memory[sp])
        high = int(self.pyboy.memory[(sp + 1) & 0xFFFF])
        return low | (high << 8)

    def read_symbol_offset(self, symbol: capture.Symbol, offset: int) -> int:
        return int(
            trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + offset),
            )
        )

    def read_addr(self, address: int) -> int:
        bank = self.symbols["wEnemyAIMoveScores"].bank if 0xD000 <= address <= 0xDFFF else 0
        return int(trace_runtime.read_byte(self.pyboy, capture.Symbol(bank, address)))


class RomContributionTraceSession:
    def __init__(
        self,
        *,
        rom: Path = capture.DEFAULT_ROM,
        symbols_path: Path = capture.DEFAULT_SYMBOLS,
    ) -> None:
        self.rom = rom
        self.symbols_path = symbols_path
        self.symbols = capture.parse_symbols(symbols_path)
        capture.require_symbols(self.symbols)
        require_hook_symbols(self.symbols)
        self.symbol_index = SymbolIndex(self.symbols, build_rule_map())
        self.move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
        pyboy_class = trace_runtime.load_pyboy(
            "PyBoy is required for ROM contribution tracing"
        )
        self.pyboy = pyboy_class(str(rom), window="null", sound=False, log_level="ERROR")
        trace_runtime.disable_realtime(self.pyboy)
        self.tracer = RomContributionTracer(
            self.pyboy,
            self.symbols,
            self.symbol_index,
            self.move_names,
        )
        register_hooks(self.pyboy, self.symbol_index.hook_targets(), self.tracer)
        self.basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )

    def __enter__(self) -> "RomContributionTraceSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.pyboy.stop(save=False)

    def run(
        self,
        *,
        save_state: Path,
        button: str = "a",
        button_delay: int = 8,
        watch_frames: int = 60,
        metadata: dict[str, str] | None = None,
        memory_patches: list[MemoryPatch] | None = None,
    ) -> dict[str, Any]:
        if not save_state.exists():
            raise PreferenceDataError(f"missing save-state: {save_state}")

        patches = memory_patches or []
        self.tracer.reset(memory_patches=patches)
        with save_state.open("rb") as fh:
            self.pyboy.load_state(fh)
        apply_memory_patches(self.pyboy, self.symbols, patches)
        clear_chosen_move(self.pyboy, self.symbols)
        if button:
            self.pyboy.button(button, delay=button_delay)

        final_values = None
        for _frame in range(watch_frames + 1):
            values = capture.read_trace_values(self.pyboy, self.symbols)
            if values["wBossAITraceChosenMove"][0] != 0:
                final_values = values
                break
            self.pyboy.tick(1, False, False)
        self.tracer.close_pending(trigger="replay_end")
        if final_values is None:
            raise PreferenceDataError(
                f"no boss move choice observed within {watch_frames} frames"
            )

        basis = dict(self.basis)
        if metadata:
            basis.update(metadata)
        return build_report(
            save_state=save_state,
            basis=basis,
            values=final_values,
            events=self.tracer.events,
            rule_entries=self.tracer.rule_entries,
            predicate_branch_entries=self.tracer.predicate_branch_entries,
            move_names=self.move_names,
            memory_patches=patches,
        )


def run_rom_contribution_trace(
    *,
    save_state: Path,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = 60,
    metadata: dict[str, str] | None = None,
    memory_patches: list[MemoryPatch] | None = None,
) -> dict[str, Any]:
    with RomContributionTraceSession(rom=rom, symbols_path=symbols_path) as session:
        return session.run(
            save_state=save_state,
            button=button,
            button_delay=button_delay,
            watch_frames=watch_frames,
            metadata=metadata,
            memory_patches=memory_patches,
        )


def run_rom_contribution_trace_for_route(
    *,
    boss_id: str,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    battery_save: Path | None = None,
    out_dir: Path | None = None,
    input_wait_frames: int = 0,
    max_a_presses: int = 0,
    metadata: dict[str, str] | None = None,
    memory_patches: list[MemoryPatch] | None = None,
) -> dict[str, Any]:
    from tools.trace import boss_ai_state_factory as factory

    if boss_id not in factory.ROUTES:
        known = ", ".join(sorted(factory.ROUTES))
        raise PreferenceDataError(f"unknown boss route {boss_id!r}; known: {known}")
    route = factory.ROUTES[boss_id]
    battery = battery_save if battery_save is not None else factory.DEFAULT_BATTERY_SAVE
    output = out_dir if out_dir is not None else factory.DEFAULT_OUT_DIR
    args = Namespace(
        rom=rom,
        battery_save=battery,
        out_dir=output,
        input_wait_frames=input_wait_frames,
        max_a_presses=max_a_presses,
        log_every=20,
    )

    symbols = capture.parse_symbols(symbols_path)
    capture.require_symbols(symbols)
    factory.require_symbols(symbols, [route])
    require_hook_symbols(symbols)
    event_constants = factory.parse_simple_consts(factory.EVENT_FLAGS)
    map_constants = factory.parse_map_consts(factory.MAP_CONSTANTS)
    trainer_constants = factory.parse_trainer_consts(factory.TRAINER_CONSTANTS)
    trainer_constant = factory.expected_trainer(route, trainer_constants)

    symbol_index = SymbolIndex(symbols, build_rule_map())
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    work_rom = factory.prepare_work_rom(args)
    pyboy = factory.open_pyboy(work_rom)
    tracer = RomContributionTracer(
        pyboy,
        symbols,
        symbol_index,
        move_names,
        memory_patches=memory_patches,
    )
    log: list[str] = [
        f"ROUTE {route.capture_id}",
        "MODE contribution_trace",
        f"ROM_SOURCE {capture.display_path(rom)}",
        f"ROM_WORK {capture.display_path(work_rom)}",
        f"BATTERY_SAVE {capture.display_path(battery)}",
    ]
    try:
        register_hooks(pyboy, symbol_index.hook_targets(), tracer)
        frame = factory.boot_continue(pyboy, symbols, log)
        frame = factory.setup_route_entry(
            pyboy,
            route,
            symbols,
            event_constants,
            map_constants,
            output,
            log,
            frame,
        )
        apply_memory_patches(pyboy, symbols, memory_patches or [])
        values, frame = drive_route_until_choice(
            pyboy,
            route,
            trainer_constant,
            symbols,
            args,
            log,
            frame,
        )
        tracer.close_pending(trigger="route_replay_end")
        basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )
        if metadata:
            basis.update(metadata)
        report = build_report(
            save_state=work_rom,
            save_state_label=f"route:{route.capture_id}",
            basis=basis,
            values=values,
            events=tracer.events,
            rule_entries=tracer.rule_entries,
            predicate_branch_entries=tracer.predicate_branch_entries,
            move_names=move_names,
            memory_patches=memory_patches or [],
        )
        report["boss_route"] = route.capture_id
        report["frame"] = frame
        report["work_rom"] = capture.display_path(work_rom)
        return report
    finally:
        pyboy.stop(save=False)


def drive_route_until_choice(
    pyboy: Any,
    route: Any,
    trainer_constant: Any,
    symbols: dict[str, capture.Symbol],
    args: Namespace,
    log: list[str],
    frame: int,
) -> tuple[dict[str, list[int]], int]:
    from tools.trace import boss_ai_state_factory as factory

    input_wait_frames = (
        route.input_wait_frames
        if args.input_wait_frames == 0
        else args.input_wait_frames
    )
    for button_name in route.prime_buttons:
        factory.press(pyboy, button_name, input_wait_frames)
        frame += input_wait_frames
        log.append(factory.watch_line(pyboy, symbols, frame, f"PRIME_{button_name.upper()}"))

    max_presses = args.max_a_presses or route.max_a_presses
    for step in range(max_presses):
        factory.press(pyboy, "a", input_wait_frames)
        frame += input_wait_frames
        values = capture.read_trace_values(pyboy, symbols)
        chosen = values["wBossAITraceChosenMove"][0]
        if step % args.log_every == 0 or chosen:
            log.append(factory.watch_line(pyboy, symbols, frame, f"DRIVE_A_{step + 1:03d}"))
        if not chosen:
            continue
        trainer_class = factory.read_one(pyboy, symbols, "wOtherTrainerClass")
        trainer_id = factory.read_one(pyboy, symbols, "wOtherTrainerID")
        if (
            trainer_class != trainer_constant.class_id
            or trainer_id != trainer_constant.trainer_id
        ):
            raise PreferenceDataError(
                f"{route.capture_id}: got chosen move for trainer "
                f"{trainer_class:02x}:{trainer_id:02x}, expected "
                f"{trainer_constant.class_id:02x}:{trainer_constant.trainer_id:02x}"
            )
        return values, frame

    raise PreferenceDataError(
        f"{route.capture_id}: no chosen move observed within {max_presses} A presses"
    )


def register_hooks(
    pyboy: Any,
    targets: list[HookTarget],
    tracer: RomContributionTracer,
) -> None:
    targets_by_address: dict[tuple[int, int], list[HookTarget]] = {}
    for target in targets:
        targets_by_address.setdefault((target.bank, target.address), []).append(target)
    for (bank, address), grouped in targets_by_address.items():
        pyboy.hook_register(bank, address, hook_callback, (tracer, grouped))


def hook_callback(context: tuple[RomContributionTracer, list[HookTarget]]) -> None:
    tracer, targets = context
    tracer.handle_hook(targets)


def hook_order(target: HookTarget) -> int:
    return {"control": 0, "rule": 1, "predicate_branch": 2, "score_helper": 3}[
        target.kind
    ]


def clear_chosen_move(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
) -> None:
    symbol = symbols["wBossAITraceChosenMove"]
    if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, symbol.address] = 0
            return
        except Exception:
            pass
    pyboy.memory[symbol.address] = 0


def parse_memory_patch(text: str) -> MemoryPatch:
    lhs, sep, rhs = text.partition("=")
    if sep != "=" or not lhs or not rhs:
        raise PreferenceDataError(
            f"memory patch must look like SYMBOL=VALUE or SYMBOL+OFFSET=VALUE: {text}"
        )
    symbol_name, offset = parse_patch_location(lhs)
    value = int(rhs, 0)
    if not 0 <= value <= 0xFF:
        raise PreferenceDataError(f"memory patch value must be a byte: {text}")
    return MemoryPatch(symbol_name=symbol_name, offset=offset, value=value)


def parse_patch_location(text: str) -> tuple[str, int]:
    symbol_name, plus, offset_text = text.partition("+")
    if not symbol_name:
        raise PreferenceDataError(f"memory patch symbol is empty: {text}")
    offset = int(offset_text, 0) if plus else 0
    if offset < 0:
        raise PreferenceDataError(f"memory patch offset must be non-negative: {text}")
    return symbol_name, offset


def apply_memory_patches(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    patches: list[MemoryPatch],
) -> None:
    for patch in patches:
        symbol = symbols.get(patch.symbol_name)
        if symbol is None:
            raise PreferenceDataError(f"unknown memory patch symbol: {patch.symbol_name}")
        write_symbol_offset(pyboy, symbol, patch.offset, patch.value)


def write_symbol_offset(
    pyboy: Any,
    symbol: capture.Symbol,
    offset: int,
    value: int,
) -> None:
    address = symbol.address + offset
    value &= 0xFF
    if 0xD000 <= address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, address] = value
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = symbol.bank
            try:
                pyboy.memory[address] = value
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[address] = value


def memory_patches_to_json(patches: list[MemoryPatch]) -> list[dict[str, Any]]:
    return [
        {
            "symbol_name": patch.symbol_name,
            "offset": patch.offset,
            "value": patch.value,
        }
        for patch in patches
    ]


def build_report(
    *,
    save_state: Path,
    save_state_label: str | None = None,
    basis: dict[str, str],
    values: dict[str, list[int]],
    events: list[dict[str, Any]],
    rule_entries: list[dict[str, Any]],
    predicate_branch_entries: list[dict[str, Any]],
    move_names: dict[int, str],
    memory_patches: list[MemoryPatch],
) -> dict[str, Any]:
    changed = [event for event in events if event["changed"]]
    executed_rule_ids = sorted(
        rule_ids_from_events(rule_entries)
        | rule_ids_from_events(predicate_branch_entries)
        | rule_ids_from_events(events)
    )
    return {
        "schema_version": 1,
        "source": "trace_rom_pyboy_hooks",
        "save_state": save_state_label or trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "chosen": {
            "move_id": values["wBossAITraceChosenMove"][0],
            "move_name": move_names.get(
                values["wBossAITraceChosenMove"][0],
                f"#{values['wBossAITraceChosenMove'][0]:02x}",
            ),
            "slot_index": values["wCurEnemyMoveNum"][0],
        },
        "memory_patches": memory_patches_to_json(memory_patches),
        "move_ids": values["wEnemyMonMoves"],
        "move_scores": values["wEnemyAIMoveScores"],
        "pre_model_scores": values["wBossAITracePreModelScores"],
        "post_model_scores": values["wBossAITracePostModelScores"],
        "rule_entry_count": len(rule_entries),
        "executed_rule_count": len(executed_rule_ids),
        "executed_rule_ids": executed_rule_ids,
        "rule_entries": rule_entries,
        "predicate_branch_entry_count": len(predicate_branch_entries),
        "predicate_branch_entries": predicate_branch_entries,
        "event_count": len(events),
        "changed_event_count": len(changed),
        "events": events,
        "known_limits": [
            "Trace events are captured by PyBoy execution hooks, not by an in-ROM WRAM ring buffer.",
            "Score events record score helper deltas and source labels, while rule entries record dynamic rule-label execution.",
            "Predicate branch entries record selected executable public-info branch labels, not full false-path coverage.",
            "Public-read evidence includes selected branch legal-input snapshots, but not full dynamic memory-read slicing yet.",
        ],
    }


def format_rom_contribution_trace(report: dict[str, Any], *, limit: int = 80) -> str:
    chosen = report["chosen"]
    lines = [
        "Boss AI ROM contribution trace",
        (
            f"source={report['source']} save_state={report['save_state']} "
            f"events={report['event_count']} changed={report['changed_event_count']} "
            f"rule_entries={report.get('rule_entry_count', 0)} "
            f"predicate_branches={report.get('predicate_branch_entry_count', 0)}"
        ),
        (
            f"chosen={chosen['move_name']}#{chosen['move_id']} "
            f"slot={chosen['slot_index']}"
        ),
        (
            "scores: "
            f"pre={csv(report['pre_model_scores'])} "
            f"post={csv(report['post_model_scores'])} "
            f"final={csv(report['move_scores'])}"
        ),
        "",
        f"First {limit} score events:",
    ]
    for event in report["events"][:limit]:
        candidate = event["candidate"]
        source = event["source"]
        change = "*" if event["changed"] else " "
        lines.append(
            f"  {change} {event['index']:03d} "
            f"slot={candidate['slot_index']} {candidate['move_name']} "
            f"{event['operation']} a={event['amount_register_a']} "
            f"{event['score_before']}->{event['score_after']} "
            f"delta={event['delta']:+d}"
        )
        lines.append(
            "      "
            f"{source.get('rule_id') or source.get('full_symbol')} "
            f"callsite={source.get('callsite_symbol', '')}"
        )
    if len(report["events"]) > limit:
        lines.append(f"  ... {len(report['events']) - limit} more")
    rule_entries = report.get("rule_entries", [])
    if rule_entries:
        lines.append("")
        lines.append(f"First {min(limit, len(rule_entries))} rule entries:")
        for entry in rule_entries[:limit]:
            source = entry.get("source", {})
            candidate = entry.get("candidate", {})
            move_struct = entry.get("move_struct", {})
            effect = move_struct.get("effect", "?") if isinstance(move_struct, dict) else "?"
            lines.append(
                f"  {entry['index']:03d} "
                f"slot={candidate.get('slot_index', -1)} "
                f"effect={effect} "
                f"{source.get('rule_id') or source.get('full_symbol', '')}"
            )
        if len(rule_entries) > limit:
            lines.append(f"  ... {len(rule_entries) - limit} more")
    predicate_entries = report.get("predicate_branch_entries", [])
    if predicate_entries:
        lines.append("")
        lines.append(f"First {min(limit, len(predicate_entries))} predicate branches:")
        for entry in predicate_entries[:limit]:
            predicate = entry.get("predicate", {})
            candidate = entry.get("candidate", {})
            lines.append(
                f"  {entry['index']:03d} "
                f"slot={candidate.get('slot_index', -1)} "
                f"{predicate.get('predicate_id', '')}="
                f"{predicate.get('outcome', '')}"
            )
        if len(predicate_entries) > limit:
            lines.append(f"  ... {len(predicate_entries) - limit} more")
    lines.append("")
    lines.append("Known limits:")
    for limit_text in report["known_limits"]:
        lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def write_rom_contribution_trace_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_rom_contribution_trace(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreferenceDataError(f"missing ROM contribution trace: {path}") from exc
    if not isinstance(data, dict):
        raise PreferenceDataError(f"ROM contribution trace is not an object: {path}")
    if data.get("source") != "trace_rom_pyboy_hooks":
        raise PreferenceDataError(f"unsupported ROM contribution trace source: {path}")
    return data


def summarize_rom_contribution_trace(
    report: dict[str, Any],
    *,
    artifact_path: Path | None = None,
) -> dict[str, Any]:
    events = [event for event in report.get("events", []) if isinstance(event, dict)]
    rule_entries = [
        event for event in report.get("rule_entries", []) if isinstance(event, dict)
    ]
    predicate_branch_entries = [
        event
        for event in report.get("predicate_branch_entries", [])
        if isinstance(event, dict)
    ]
    changed_events = [event for event in events if event.get("changed")]
    covered_rule_ids = sorted(rule_ids_from_events(events))
    changed_rule_ids = sorted(rule_ids_from_events(changed_events))
    executed_rule_ids = sorted(
        rule_ids_from_events(rule_entries)
        | rule_ids_from_events(predicate_branch_entries)
        | set(covered_rule_ids)
    )
    operation_counts = count_event_values(events, "operation")
    changed_operation_counts = count_event_values(changed_events, "operation")
    classification_counts = count_source_values(events, "classification")
    changed_classification_counts = count_source_values(changed_events, "classification")
    executed_classification_counts = count_source_values(
        [*rule_entries, *predicate_branch_entries, *events],
        "classification",
    )
    predicate_counts = count_predicate_values(predicate_branch_entries, "predicate_id")
    predicate_outcome_counts = count_predicate_outcomes(predicate_branch_entries)
    predicate_snapshot_count = count_predicate_public_input_snapshots(
        predicate_branch_entries
    )
    result = {
        "available": True,
        "source": report.get("source", ""),
        "save_state": report.get("save_state", ""),
        "boss_route": report.get("boss_route", ""),
        "artifact": relative_artifact_path(artifact_path) if artifact_path else "",
        "trace_rom_sha256": report.get("trace_basis", {}).get("trace_rom_sha256", ""),
        "trace_symbols_sha256": report.get("trace_basis", {}).get(
            "trace_symbols_sha256",
            "",
        ),
        "event_count": int(report.get("event_count", len(events))),
        "changed_event_count": int(report.get("changed_event_count", len(changed_events))),
        "rule_entry_count": int(report.get("rule_entry_count", len(rule_entries))),
        "predicate_branch_entry_count": int(
            report.get("predicate_branch_entry_count", len(predicate_branch_entries))
        ),
        "predicate_public_input_snapshot_count": predicate_snapshot_count,
        "executed_rule_count": len(executed_rule_ids),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "executed_rule_ids": executed_rule_ids,
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": operation_counts,
        "changed_operation_counts": changed_operation_counts,
        "executed_classification_counts": executed_classification_counts,
        "classification_counts": classification_counts,
        "changed_classification_counts": changed_classification_counts,
        "predicate_counts": predicate_counts,
        "predicate_outcome_counts": predicate_outcome_counts,
        "unmapped_event_count": count_unmapped_events(events),
        "unmapped_rule_entry_count": count_unmapped_events(rule_entries),
        "unmapped_predicate_branch_entry_count": count_unmapped_events(
            predicate_branch_entries
        ),
        "changed_unmapped_event_count": count_unmapped_events(changed_events),
        "candidate_count": len(candidate_keys(events)),
        "changed_candidate_count": len(candidate_keys(changed_events)),
        "chosen": report.get("chosen", {}),
        "known_limits": report.get("known_limits", []),
    }
    return result


def summarize_rom_contribution_trace_paths(paths: list[Path]) -> dict[str, Any]:
    loaded = [
        summarize_rom_contribution_trace(
            load_rom_contribution_trace(path),
            artifact_path=path,
        )
        for path in paths
        if path.exists()
    ]
    if not loaded:
        return {
            "available": False,
            "artifact_count": 0,
            "event_count": 0,
            "changed_event_count": 0,
            "rule_entry_count": 0,
            "predicate_branch_entry_count": 0,
            "predicate_public_input_snapshot_count": 0,
            "executed_rule_count": 0,
            "covered_rule_count": 0,
            "changed_rule_count": 0,
            "executed_rule_ids": [],
            "covered_rule_ids": [],
            "changed_rule_ids": [],
            "operation_counts": {},
            "changed_operation_counts": {},
            "executed_classification_counts": {},
            "classification_counts": {},
            "changed_classification_counts": {},
            "predicate_counts": {},
            "predicate_outcome_counts": {},
            "unmapped_event_count": 0,
            "unmapped_rule_entry_count": 0,
            "unmapped_predicate_branch_entry_count": 0,
            "changed_unmapped_event_count": 0,
            "candidate_count": 0,
            "changed_candidate_count": 0,
            "artifacts": [],
        }

    covered_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["covered_rule_ids"]
        }
    )
    changed_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["changed_rule_ids"]
        }
    )
    executed_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["executed_rule_ids"]
        }
    )
    return {
        "available": True,
        "artifact_count": len(loaded),
        "event_count": sum(int(summary["event_count"]) for summary in loaded),
        "changed_event_count": sum(
            int(summary["changed_event_count"]) for summary in loaded
        ),
        "rule_entry_count": sum(int(summary["rule_entry_count"]) for summary in loaded),
        "predicate_branch_entry_count": sum(
            int(summary["predicate_branch_entry_count"]) for summary in loaded
        ),
        "predicate_public_input_snapshot_count": sum(
            int(summary["predicate_public_input_snapshot_count"])
            for summary in loaded
        ),
        "executed_rule_count": len(executed_rule_ids),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "executed_rule_ids": executed_rule_ids,
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": merge_counts(
            summary["operation_counts"] for summary in loaded
        ),
        "changed_operation_counts": merge_counts(
            summary["changed_operation_counts"] for summary in loaded
        ),
        "executed_classification_counts": merge_counts(
            summary["executed_classification_counts"] for summary in loaded
        ),
        "classification_counts": merge_counts(
            summary["classification_counts"] for summary in loaded
        ),
        "changed_classification_counts": merge_counts(
            summary["changed_classification_counts"] for summary in loaded
        ),
        "predicate_counts": merge_counts(
            summary["predicate_counts"] for summary in loaded
        ),
        "predicate_outcome_counts": merge_counts(
            summary["predicate_outcome_counts"] for summary in loaded
        ),
        "unmapped_event_count": sum(
            int(summary["unmapped_event_count"]) for summary in loaded
        ),
        "unmapped_rule_entry_count": sum(
            int(summary["unmapped_rule_entry_count"]) for summary in loaded
        ),
        "unmapped_predicate_branch_entry_count": sum(
            int(summary["unmapped_predicate_branch_entry_count"])
            for summary in loaded
        ),
        "changed_unmapped_event_count": sum(
            int(summary["changed_unmapped_event_count"]) for summary in loaded
        ),
        "candidate_count": sum(int(summary["candidate_count"]) for summary in loaded),
        "changed_candidate_count": sum(
            int(summary["changed_candidate_count"]) for summary in loaded
        ),
        "artifacts": loaded,
    }


def resolve_rom_contribution_trace_paths(paths: list[Path] | None) -> list[Path]:
    if paths is not None:
        return paths
    return [
        path
        for path in (
            DEFAULT_ROM_CONTRIBUTION_TRACE_PATH,
            DEFAULT_ROM_CONTRIBUTION_TRACE_PROBE_PATH,
        )
        if path.exists()
    ]


def require_hook_symbols(symbols: dict[str, capture.Symbol]) -> None:
    missing = [
        name
        for name in [*SCORE_HELPERS, *CONTROL_HOOKS]
        if name not in symbols
    ]
    if missing:
        raise PreferenceDataError("missing hook symbols: " + ", ".join(missing))


def build_rule_lookup(rule_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rule in rule_map["rules"]:
        full_symbol = full_symbol_for_rule(rule)
        if not full_symbol:
            continue
        out[full_symbol] = rule
    return out


def full_symbol_for_rule(rule: dict[str, Any]) -> str:
    label = str(rule["source_label"])
    if label.startswith("."):
        if not isinstance(rule.get("parent_label"), str):
            return ""
        return f"{rule['parent_label']}{label}"
    return label


def is_executable_hook_label(full_symbol: str) -> bool:
    label = full_symbol.rsplit(".", 1)[-1]
    if label.startswith("BossAI") and not label.startswith("BossAI_"):
        return False
    return True


def nearest_name(items: list[tuple[int, str]], address: int) -> str:
    name = ""
    for item_address, item_name in items:
        if item_address > address:
            break
        name = item_name
    return name


def csv(values: list[int]) -> str:
    return ",".join(str(value) for value in values)


def rule_ids_from_events(events: list[dict[str, Any]]) -> set[str]:
    rule_ids = set()
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if rule_id:
            rule_ids.add(rule_id)
    return rule_ids


def candidate_keys(events: list[dict[str, Any]]) -> set[tuple[str, int, int]]:
    keys = set()
    for event in events:
        candidate = event.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        keys.add(
            (
                str(candidate.get("kind", "")),
                int(candidate.get("slot_index", -1)),
                int(candidate.get("move_id", 0)),
            )
        )
    return keys


def unknown_candidate() -> dict[str, Any]:
    return {
        "kind": "unknown_score_pointer",
        "slot_index": -1,
        "slot": 0,
        "move_id": 0,
        "move_name": "",
    }


def count_event_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        value = str(event.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_source_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        value = str(source.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        predicate = event.get("predicate", {})
        if not isinstance(predicate, dict):
            continue
        value = str(predicate.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_outcomes(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        predicate = event.get("predicate", {})
        if not isinstance(predicate, dict):
            continue
        predicate_id = str(predicate.get("predicate_id", ""))
        outcome = str(predicate.get("outcome", ""))
        if not predicate_id or not outcome:
            continue
        key = f"{predicate_id}:{outcome}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_public_input_snapshots(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        snapshot = event.get("public_input_snapshot")
        if isinstance(snapshot, dict) and snapshot:
            count += 1
    return count


def count_unmapped_events(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        if not rule_ids_from_events([event]):
            count += 1
    return count


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def relative_artifact_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class SimpleTraceArgs:
    rom: Path
    symbols: Path
