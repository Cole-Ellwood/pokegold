# Scoping: headless board → `rom-switch-materialize` scenario exporter

Status: scoping pass only. No exporter code shipped yet.

## Goal

Per the 2026-05-25 brief option 1: convert a headless battle board (or a
constrained JSON board) into the existing `rom_switch_materialize`
scenario format, run `rom-switch-materialize` to get a ROM-observed
`switch_confidence` + threshold, then feed the exact `switch_roll`
output into headless `boss_ai_switch_roll`. This is the highest-value
slice in the brief because it would close the board-to-confidence
gap without inventing a Python boss-AI reimplementation.

## What the scenario format actually accepts today

Reading [`tools/boss_ai_debugger/rom_switch_materialize.py`](tools/boss_ai_debugger/rom_switch_materialize.py)
end-to-end and inspecting real `.local/tmp/switch_sack_*.jsonl` files,
the scenario shape is **not** an arbitrary battle board. A scenario is:

| Field | Type | Effect |
|---|---|---|
| `id` | str | Scenario name, used in verdicts |
| `family` | str | Must be in `SUPPORTED_FAMILIES = ("switch_sack",)`; other families are skipped |
| `tier` | str | `early`/`mid`/`late`; mapped to `wBossAITier` + `wBossAITierWeightRow` |
| `expectation.condition_tags` | list[str] | Drives which tagged toggles fire inside `switch_materialization_patches` |
| `moves[]`, `expectation.*_action_ids`, `policy_case` | various | Human-judged labels for the right action; consumed by `switch_verdict_from_report`, not by the ROM materialization itself |

Critically, [`switch_materialization_patches`](tools/boss_ai_debugger/rom_switch_materialize.py:257)
hard-codes the fixture:

- Player active: **Starmie**, types overridden to **Ground/Ground**
- Enemy active: **Qwilfish**, types Poison/Water
- Enemy bench: **Gengar** at party index 1 (`wOTPartyMon2*`)
- HP/MaxHP: only two integers per side, both derived from two tags
  (`defensive_sack_owner` → enemy HP 22; `active_pressure_converts` →
  player HP 20; otherwise 80)
- Statuses, screens, item, cooldowns, plan id: all zero or constant
- `wPlayerUsedMoves[0] = 0x59`, the rest cleared

The scenario JSON cannot specify arbitrary species, levels, IVs, EVs,
stat stages, sub-statuses, weather, screens, or move sets. It can
toggle a handful of hardcoded conditions via condition tags.

## Gap from arbitrary headless board to a runnable scenario

The headless simulator's `BattleState` carries: species, level, types,
HP, max HP, stats, stat stages, status, toxic counter, sleep counter,
sub-statuses, item, moves with PP, weather, weather count, spike
layers, safeguard, substitute hp, party benches on both sides, etc.

That's a wide surface; the materializer can only reflect a tiny
keyhole of it. Three classes of gap:

1. **Species/types/levels mismatch.** Headless board says Haunter vs
   Cyndaquil, but the materializer always forces Starmie vs Qwilfish.
   Any switch_confidence read back is for the hardcoded board, not the
   board the headless caller was reasoning about.
2. **HP-as-tag only.** Headless carries real HP integers; the
   materializer derives HP from two condition tags. Two scenarios
   with different headless HP (e.g. 65/100 vs 30/100) both map to
   the same materializer HP if they share tags.
3. **Tag derivation is not mechanical.** `condition_tags` like
   `"active_pressure_converts"` and `"defensive_sack_owner"` are
   semantic judgments about the scenario, not direct WRAM bytes.
   Deriving them from a raw headless board would require a
   boss-AI-style classifier (which is exactly what the goal is
   trying to avoid).

## What the existing bridge already provides

Commit `4556812b` (shipped 2026-05-25 by Codex) wired
`rom-switch-materialize` output into `boss_ai_switch_roll` when the
materializer's `probability_exact` is true. Commit `0e0f8f51`
(this session) extended that with a `report_only` mode for ranged
materializer output. So the headless side can already CONSUME
materializer output; what's missing is the headless side being able
to PRODUCE the materializer's input from its own board.

Today the input is hand-written `.jsonl` scenarios.

## Minimum viable exporter options

Three honest paths, ordered by scope:

### A. Fixture-match-or-reject exporter (smallest)

Add a `headless_to_switch_sack_scenario(state, *, tags=None)` helper
that:

1. Asserts the headless `state` matches the hardcoded fixture shape:
   - Player active species == Starmie OR the caller explicitly
     overrides species, and the headless player types are
     Ground/Ground
   - Enemy active species == Qwilfish, types Poison/Water
   - Enemy bench at index 0 == Gengar
   - Any condition not modeled by tags must be at the default (e.g.
     no status, no item, no stat stages, no weather, no screens)
2. Maps headless HP to the tag set:
   - Enemy HP ≤ 30 → `defensive_sack_owner`
   - Player HP ≤ 30 → `active_pressure_converts`
3. Lets the caller pass `tags` (e.g. `wincon_preservation`) for
   conditions headless doesn't yet model
4. Emits a single-scenario `.jsonl` consumable by
   `run_rom_switch_materialization_from_path`

**Proof boundary:** This proves the *fixture* board's switch
behavior, not the headless caller's board. Headless boards that
don't fit the fixture are rejected with a clear "not in fixture
domain" error rather than silently being mapped to a wrong scenario.

**Use case:** any headless caller already debugging the canonical
Jasmine switch-loop case can stop hand-writing JSONL and let the
exporter generate it from their existing `BattleState`.

**Not solved:** arbitrary boards (e.g. Morty's Haunter→Gengar from
the brief's option 3) still can't be materialized.

### B. Parameterized-fixture exporter (medium)

Extend `switch_materialization_patches` to accept caller-supplied
species/types/HP/level overrides for the active and bench slots, then
expose those as new scenario fields. Add corresponding headless
exporter fields. This widens the materializer's accepted input domain
but does NOT add new condition behaviors — it just makes more boards
reflect into ROM.

**Risk:** Existing `boss_ai_switch_predispatch_fixture` and the manifest
trace-basis hash (`audit/boss_ai_trace/live_capture_manifest.json`)
may be invalidated, since changing the patched fixture changes the
captured ROM behavior. Needs a manifest refresh.

### C. Full board materializer (largest)

Make the materializer accept a complete headless `BattleState` JSON
and patch every relevant WRAM field. This is essentially writing a
`headless_state → ROM_save_state` serializer for the boss-AI subset.
Out of scope for one slice; would need its own multi-iteration
project.

## Recommended first slice

**Ship A first.** It's the smallest move that converts the existing
bridge from "consumer-only" to "round-trippable for one canonical
board." It surfaces the fixture-domain constraint explicitly (better
than silent misuse), and it gives Codex/Claude a concrete starting
shape to extend toward B if needed.

Concrete deliverable for slice A:

1. `tools/headless_battle/rom_switch_scenario_export.py` with
   `headless_to_switch_sack_scenario(state, *, tags=None,
   scenario_id="exported", policy_case=None) -> dict` that returns a
   single scenario dict matching the `family=switch_sack` shape.
2. Strict domain checks that raise `SimulationInputError` (already
   used by the simulator) with a specific message naming the field
   that's outside the fixture.
3. `tools/headless_battle/tests/test_rom_switch_scenario_export.py`:
   - happy path: canonical Starmie/Qwilfish/Gengar board with default
     HP → no exception, scenario shape valid
   - tag toggle: low enemy HP → `defensive_sack_owner` in tags
   - rejection: wrong player species, wrong enemy bench, present
     status/item/weather → raises with reason
4. `tools/audit/check_headless_battle_simulator.py`: add a smoke check
   that the canonical scenario round-trips into `switch_roll_frequency`
   (without running ROM materialization — that's covered by the
   existing `rom-switch-materialize` audits).
5. README + `tools/debugger/next_steps.py`: name the new proof, with
   the explicit "fixture-domain only; arbitrary boards still need
   B or C" boundary.

## What to NOT do in this slice

- Do not modify `switch_materialization_patches` (that's slice B).
- Do not run `rom-switch-materialize` end-to-end as part of the
  headless simulator audit (slow; the existing
  `tools/audit/check_boss_ai_switch_materialize*.py` audits cover
  the ROM side).
- Do not claim live boss-AI scoring is solved.
- Do not silently lossy-map arbitrary boards onto the fixture.

## Open questions for slice B / C

- Whose responsibility is the manifest refresh after a
  `switch_materialization_patches` schema change? (probably the slice
  author + a re-captured live state)
- Can the fixture be split into a base + an overlay so existing
  scenarios stay byte-stable while new scenarios get richer
  overrides?
- What's the smallest set of WRAM fields that has to be parameterized
  to cover the Morty Haunter→Gengar case from option 3 of the
  brief?

## References

- [`tools/boss_ai_debugger/rom_switch_materialize.py`](tools/boss_ai_debugger/rom_switch_materialize.py)
- [`tools/headless_battle/simulator.py`](tools/headless_battle/simulator.py) `boss_ai_switch_roll_results`, `boss_ai_switch_roll_source`
- `.local/tmp/switch_sack_probe.jsonl` (real generated scenario shape)
- `audit/boss_ai_trace/live_capture_manifest.json` (manifest gating
  the materialization base state)
