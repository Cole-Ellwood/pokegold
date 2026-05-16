# pgoal Packet 046 — Baseline Arm — 2026-05-16 — smogtours-gen2ou-936075 (p2 KeshBa45)

Source: https://replay.pokemonshowdown.com/smogtours-gen2ou-936075
Mode: side-known reconstructed; p2 (KeshBa45); species-only peek of full
log per `workspace/pgoal_046_inputs.md`.
Arm: **baseline** — loads `live_core.md` + `heuristic_core/*` (v1 paths).
Contamination control: dual-freeze per turn (this arm frozen BEFORE
intervention arm frozen, both BEFORE actual reveal).

## Score Summary (filled at packet end)

```
Decisions:                       _/30
Top-match:                       _/30
Acceptable-match:                _/30
Positive-selection:              _/30
Route-converting move chosen:    _/30
Branch-punish chosen:            _/30
Actual in frozen top three:      _/30
Severe blunders:                 _/30
Hidden-info errors:              _/30
State errors:                    _/30
Mechanics errors:                _/30
Earliest meaningful error:       Turn _
```

## Pre-freeze loaded cards (baseline always-load)

- `live_core.md` (v1, with Load-Required Triggers from cf87f141)
- `active_context.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/name_current_owner.md`

Triggered cards per turn listed in each turn's section.

## Turn 1

Public state: turn-1 lead RPS. p1a Jynx 100/100 (leoperi99). p2a Zapdos
100/100 (KeshBa45). No moves revealed.

Triggered cards loaded: `heuristic_core/reset_loop_denial.md` (Rest in
package strong prior — Snorlax behind on p2 team), `heuristic_core/spend_or_save_piece.md`
(Zapdos is the unique special breaker on p2; LK Jynx threatens spending
Zapdos's slot for a slow first move), `heuristic_core/converter_before_script.md`
(Thunder Wave converter vs Jynx threat; switch is the safe script).

My (p2) freeze:
- Recommended: Thunder Wave on Jynx.
- Confidence: 45/30/25.
- Route reason: Para'd Jynx is route-crippled — sleep clause preserved
  (Jynx is the LK piece on p1), Jynx's future LK threat neutered.
- Top three:
  1. Thunder Wave — defensive converter; deny LK leverage on Jynx; Zapdos
     Spe 100 > Jynx Spe 95, so TW fires first.
  2. Switch Forretress — anti-LK Spikes setter; Forry absorbs sleep
     cheaply; sets Spikes pressure.
  3. Drill Peck on Jynx — ~50% chip on Jynx (Flying neutral on Ice/Psy);
     risks LK in return but trades meaningful damage.
- Serious alternatives: Switch Tyranitar (Psychic immune via Dark) — but
  Ice Beam 2x on TTar is real damage; downranked.
- Rejected tempting safe line: Switch Snorlax (Snorlax eats LK = sleep
  clause BURNED on the route piece; bad trade).
- Worst plausible branch: Jynx Mean Look variant locks Zapdos. Rare;
  accept tail risk.
- Public-info tier: Jynx LK / Ice Beam / Psychic = `strong prior`. Jynx
  Mean Look / Substitute = `possible only`.
- Branch-punish audit per top-3:
  - Thunder Wave beats LK Jynx (paras first), beats Ice Beam (lower
    threat); loses to Mean Look Jynx.
  - Switch Forretress beats LK (Forry sleeps cheaply), beats Ice Beam
    (0.5x); loses to Psychic-spam (Steel resist — fine, doesn't really
    lose).
  - Drill Peck beats stay-and-attack; loses to LK (Zapdos slept).

Actual: p2 switched Zapdos → Raikou; p1 switched Jynx → Golem.

Grade:
- top_match = 0 (Switch Raikou not in my top-3)
- acceptable_match = 1 (same route family: preserve Zapdos by switching
  out of LK-able matchup; Switch Forretress was my #2 in same family,
  Switch Raikou is faster-attacker variant of the preserve-Zapdos route)
- positive_selection = 1 (preservation of unique-role Zapdos slot)
- route_converting_move_chosen = 0 (switch, not converter)
- branch_punish_chosen = 0 (my top-1 Thunder Wave does punish LK
  branch, but actual didn't pick punisher; the route_budget call won)
- severe_blunder = 0
- hidden_info_error = 0
- state_error = 0
- mechanics_error = 0
- **top_rank_failure: route_budget** — under-weighted "preserve Zapdos
  for late-game special breaker role" relative to "para Jynx now."
  Same family as packet 045 T1 / T3 sleep-clause-budget misses. The
  `spend_or_save_piece.md` rule was loaded but did not promote
  preservation to top-1 over the active-target converter.
