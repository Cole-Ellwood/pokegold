from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.headless_battle.rom_diff import (
    assert_after_hit_differential,
    assert_accuracy_differential,
    assert_boss_ai_selector_differential,
    assert_critical_differential,
    assert_damage_variation_differential,
    assert_double_damage_differential,
    assert_flinch_turn_differential,
    assert_freeze_turn_differential,
    assert_leftovers_differential,
    assert_paralysis_turn_differential,
    assert_residual_status_differential,
    assert_sleep_turn_differential,
    assert_status_speed_differential,
    assert_turn_order_differential,
)
from tools.headless_battle.simulator import run_self_test


def main() -> int:
    try:
        run_self_test()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    print("simulator_self_test: PASS")
    try:
        diff_rows = assert_damage_variation_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in diff_rows:
        print(
            "damage_variation_diff "
            f"{row['case']}: PASS rom_damage={row['rom']['damage']} "
            f"rng_count={row['rom']['rng_count']}"
        )
    try:
        order_rows = assert_turn_order_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in order_rows:
        print(
            "turn_order_diff "
            f"{row['case']}: PASS rom_order={','.join(row['rom']['order'])} "
            f"rng_count={row['rom']['rng_count']}"
        )
    try:
        accuracy_rows = assert_accuracy_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in accuracy_rows:
        print(
            "accuracy_diff "
            f"{row['case']}: PASS rom_hit={row['rom']['hit']} "
            f"rng_count={row['rom']['rng_count']}"
        )
    try:
        critical_rows = assert_critical_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in critical_rows:
        print(
            "critical_hit_diff "
            f"{row['case']}: PASS rom_critical={row['rom']['critical']} "
            f"rng_count={row['rom']['rng_count']}"
        )
    try:
        selector_rows = assert_boss_ai_selector_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in selector_rows:
        print(
            "boss_ai_selector_diff "
            f"{row['case']}: PASS ready={row['rom']['ready']} "
            f"slot={row['rom']['selected_slot_index']}"
        )
    try:
        double_rows = assert_double_damage_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in double_rows:
        print(
            "double_damage_diff "
            f"{row['case']}: PASS rom_damage={row['rom']['damage']}"
        )
    try:
        after_hit_rows = assert_after_hit_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in after_hit_rows:
        print(
            "after_hit_diff "
            f"{row['case']}: PASS player_hp={row['rom']['player_hp']} "
            f"enemy_hp={row['rom']['enemy_hp']}"
        )
    try:
        residual_rows = assert_residual_status_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in residual_rows:
        print(
            "residual_status_diff "
            f"{row['case']}: PASS hp={row['rom']['hp']} "
            f"toxic_count={row['rom']['toxic_count']}"
        )
    try:
        leftovers_rows = assert_leftovers_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in leftovers_rows:
        print(
            "leftovers_diff "
            f"{row['case']}: PASS hp={row['rom']['hp']} "
            f"healed={row['rom']['healed']}"
        )
    try:
        paralysis_rows = assert_paralysis_turn_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in paralysis_rows:
        print(
            "paralysis_turn_diff "
            f"{row['case']}: PASS blocked={row['rom']['blocked']} "
            f"rng_count={row['rom']['rng_count']}"
        )
    try:
        sleep_rows = assert_sleep_turn_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in sleep_rows:
        print(
            "sleep_turn_diff "
            f"{row['case']}: PASS blocked={row['rom']['blocked']} "
            f"status_byte={row['rom']['status_byte']}"
        )
    try:
        freeze_rows = assert_freeze_turn_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in freeze_rows:
        print(
            "freeze_turn_diff "
            f"{row['case']}: PASS blocked={row['rom']['blocked']} "
            f"status_byte={row['rom']['status_byte']}"
        )
    try:
        flinch_rows = assert_flinch_turn_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in flinch_rows:
        print(
            "flinch_turn_diff "
            f"{row['case']}: PASS blocked={row['rom']['blocked']} "
            f"flinched_after={row['rom']['flinched_after']}"
        )
    try:
        speed_rows = assert_status_speed_differential()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: {exc}", file=sys.stderr)
        return 1
    for row in speed_rows:
        print(
            "status_speed_diff "
            f"{row['case']}: PASS speed={row['rom']['speed']}"
        )
    proc = subprocess.run(
        [sys.executable, "-m", "tools.damage_debugger.clobber_smoke"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print("Headless battle simulator audit FAILED: ROM-backed damage smoke failed.", file=sys.stderr)
        return 1
    print("Headless battle simulator audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
