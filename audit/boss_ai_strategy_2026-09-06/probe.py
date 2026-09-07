"""Read-only ROM probes supporting the strategy audit; does not patch game code.

Run from repository root: python audit/boss_ai_strategy_2026-09-06/probe.py
Each case uses a fresh emulator. Outputs describe seeded routine calls, not
complete played battles or a freshly rebuilt ROM.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.boss_ai_fixtures.harness import Mon, MOVES, SPECIES, TYPES, open_harness


def status_reopened():
    with open_harness() as h:
        h.seed_battle(Mon.of("GENGAR", 40, ["TOXIC"]),
                      Mon.of("RATTATA", 40, ["TACKLE"], status=8), tier=1,
                      scores=[20, 80, 80, 80], extra={
                          "wBossAIPlanId": 2, "wBossAIPlanPhase": 128,
                          "wBossAITierWeightRow": 0, "wOTPartyCount": 1})
        assert h.invoke("BossAI_ApplyMoveModel")
        scored = h.scores()
        assert h.invoke("BossAI_SelectMove")
        return {"player_already_poisoned": True, "plan": "STATUS_CHOKE",
                "post_model_scores": scored, "outcome": h.outcome()}


def unavailable_attack():
    rows = []
    for pp in (30, 0):
        with open_harness() as h:
            h.seed_battle(Mon.of("GENGAR", 40, ["THUNDERBOLT", "TOXIC"]),
                          Mon.of("RATTATA", 40, ["TACKLE"], hp_pct=10), tier=2)
            for side in ("Enemy", "Player"):
                for stat in ("Atk", "Def", "Spd", "SAtk", "SDef"):
                    h.wr(f"w{side}{stat}Level", 7)
            h.wr("wEnemyMonPP", pp)
            h.wr("wEnemyAIMoveScores", 80 if pp == 0 else 20)
            assert h.invoke("BossAI_ResetTurnCaches")
            assert h.invoke("BossAI_HasAnyKOMove")
            rows.append({"thunderbolt_pp": pp, "predicate": h.outcome()["carry"]})
    return rows


def public_speed():
    rows = []
    for stage, status in ((7, 0), (1, 64)):
        with open_harness() as h:
            h.seed_battle(Mon.of("GENGAR", 40, ["THUNDERBOLT"], status=status),
                          Mon.of("RATTATA", 40, ["TACKLE"]), tier=2)
            h.wr("wEnemySpdLevel", stage)
            h.wr("wPlayerSpdLevel", 7)
            assert h.invoke("BossAI_PublicEnemyFasterUncached")
            rows.append({"enemy_speed_stage_byte": stage, "enemy_status": status,
                         "predicts_enemy_faster": h.outcome()["carry"]})
    return rows


def futility_counterexample():
    # Algebraic contract test, not a claim these exact scores/deltas occur in a
    # natural battle. The routine permits both signs and CAP is currently 4.
    scores, deltas, cap = [10, 15], [4, -4], 4
    bounded, best, evaluated = list(scores), min(scores), []
    for i, score in enumerate(scores):
        if score > best + cap:
            continue
        bounded[i] = max(1, min(79, score + deltas[i]))
        best = min(best, bounded[i])
        evaluated.append(i)
    exhaustive = [max(1, min(79, s + d)) for s, d in zip(scores, deltas)]
    return {"evidence_kind": "algebraic counterexample", "scores": scores,
            "deltas": deltas, "evaluated_slots": evaluated,
            "pruned_result": bounded, "exhaustive_result": exhaustive}


def switch_weights():
    rows = []
    for typ in ("ICE", "ELECTRIC", "ROCK"):
        for tier in (1, 2, 3):
            with open_harness() as h:
                h.seed_battle(Mon.of("PIDGEOT", 40, ["GUST"]),
                              Mon.of("RATTATA", 40, ["TACKLE"]), tier=tier)
                h.wr("wCurSpecies", SPECIES["PIDGEOT"])
                h.wr("wOTPartySpecies", SPECIES["PIDGEOT"])
                h.wr_be16("wOTPartyMon1HP", 100)
                h.wr_be16("wOTPartyMon1MaxHP", 100)
                for name in ("wBossAIPlausibleTypeMaskCache", "wBossAILikelyTypeMaskCache"):
                    for i in range(4):
                        h.wr(name, 0, i)
                h.wr("wBossAIPrimaryThreatCache", 32)
                t = TYPES[typ]
                h.wr("wBossAILikelyTypeMaskCache", 1 << (t & 7), t // 8)
                assert h.invoke("BossAI_ComputeSwitchCandidateRisk", {"A": 1})
                rows.append({"likely_type": typ, "tier": tier, "risk": h.outcome()["a"]})
    return rows


def perish_escape():
    with open_harness() as h:
        h.seed_battle(Mon.of("PIDGEOT", 40, ["GUST"]),
                      Mon.of("RATTATA", 40, ["TACKLE"]), extra={
                          "wOTPartyCount": 2, "wCurOTMon": 0,
                          "wBossAIPlanId": 1, "wBossAIPlanPhase": 128,
                          "wEnemyPerishCount": 1, "wEnemySubStatus1": 16,
                          "wCurSpecies": SPECIES["PIDGEOT"]})
        for i in range(2):
            h.wr("wOTPartySpecies", SPECIES["PIDGEOT"], i)
            h.wr_be16(f"wOTPartyMon{i+1}HP", 100)
            h.wr_be16(f"wOTPartyMon{i+1}MaxHP", 100)
        assert h.invoke("BossAI_EnemyPerishEscapeUrgent")
        urgent = h.outcome()["carry"]
        assert h.invoke("BossAI_TrySwitch")
        return {"urgent": urgent, "switch_param": h.rd("wEnemySwitchMonParam"),
                "is_switching": h.rd("wEnemyIsSwitching")}


def lookahead_accumulators():
    rows = []
    for hp in (60, 64, 80, 100, 128, 130):
        with open_harness() as h:
            h.seed_battle(Mon.of("GENGAR", 40, ["THUNDERBOLT"]),
                          Mon.of("RATTATA", 40, ["TACKLE"]), tier=2, extra={
                              "wCurSpecies": SPECIES["GENGAR"],
                              "wBossAIPlanId": 1, "wBossAIPlanPhase": 128})
            h.wr_be16("wBattleMonHP", hp)
            h.wr_be16("wBattleMonMaxHP", hp)
            assert h.invoke("BossAI_ResetTurnCaches")
            assert h.invoke("BossAI_EvaluateActionLookahead", {"A": MOVES["THUNDERBOLT"]})
            a = h.outcome()["a"]
            rows.append({"synthetic_full_hp": hp, "delta": a if a < 128 else a - 256})
    return rows


if __name__ == "__main__":
    result = {
        "sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                   for name in ("pokegold.gbc", "pokegold.sym")},
        "status_reopened": status_reopened(),
        "unavailable_attack": unavailable_attack(),
        "public_speed": public_speed(),
        "futility_counterexample": futility_counterexample(),
        "switch_weights": switch_weights(),
        "perish_escape": perish_escape(),
        "lookahead_accumulators": lookahead_accumulators(),
    }
    output = Path(__file__).with_name("probe_results.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
