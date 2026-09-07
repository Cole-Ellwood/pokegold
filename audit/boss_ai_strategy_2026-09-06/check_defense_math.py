"""Compare projected defensive raises with actual combat commands."""
import json
from pathlib import Path
from tools.boss_ai_fixtures.harness import Mon, open_harness


def main():
    rows = []
    with open_harness() as h:
        h.seed_battle(Mon.of("SNORLAX", 50), Mon.of("JOLTEON", 50))
        for raw in (1, 7, 63, 255, 333, 500, 999):
            for stage in range(1, 14):
                for steps in (1, 2):
                    for already_max in (False, True):
                        for i in range(7):
                            h.wr("wEnemyStatLevels", 7, i)
                        h.wr("wEnemyDefLevel", stage)
                        h.wr_be16("wEnemyDefense", raw)
                        h.wr("wApplyStatLevelMultipliersToEnemy", 1)
                        ok = h.invoke("ApplyStatLevelMultiplierOnAllStats")
                        current = 999 if already_max else h.rd_be16("wEnemyMonDefense")
                        h.wr_be16("wEnemyMonDefense", current)
                        sp = int(h.pb.register_file.SP)
                        ok &= h.invoke("BossAI_ProjectRaisedDefense", {
                            "A":stage, "B":steps, "HL":raw, "D":current >> 8, "E":current & 255})
                        projected = [h.outcome()["a"], h.outcome()["bc"]]
                        ok &= int(h.pb.register_file.SP) == sp
                        h.wr("hBattleTurn", 1)
                        h.wr("wAttackMissed", 0)
                        h.wr("wEffectFailed", 0)
                        ok &= h.invoke("BattleCommand_DefenseUp" + ("2" if steps == 2 else ""))
                        combat = [h.rd("wEnemyDefLevel"), h.rd_be16("wEnemyMonDefense")]
                        rows.append(dict(raw=raw, stage=stage, steps=steps, current=current,
                            projected=projected, combat=combat, passed=ok and projected == combat))
    Path(__file__).with_name("defense_math.json").write_text(json.dumps(rows, indent=2)+"\n")
    failures = [row for row in rows if not row["passed"]]
    print(f"{len(rows)-len(failures)}/{len(rows)} defensive stat checks passed")
    for row in failures:
        print(row)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
