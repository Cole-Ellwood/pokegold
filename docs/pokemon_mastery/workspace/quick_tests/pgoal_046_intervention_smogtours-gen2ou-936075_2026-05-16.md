# pgoal Packet 046 — Intervention Arm — 2026-05-16 — smogtours-gen2ou-936075 (p2 KeshBa45)

Source: https://replay.pokemonshowdown.com/smogtours-gen2ou-936075
Mode: side-known reconstructed; p2 (KeshBa45); species-only peek of full
log per `workspace/pgoal_046_inputs.md`.
Arm: **intervention** — loads `live_core_v2.md` + `heuristic_core_v2/*`
(v2 paths). Uses audit-first workflow (Steps 1-5).
Contamination control: dual-freeze per turn (this arm frozen AFTER
baseline arm, BEFORE actual reveal). Must NOT match-rationalize the
baseline pick — audit step would reveal cheating.

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

## Pre-freeze loaded cards (intervention always-load)

- `live_core_v2.md` (v2 audit-first workflow)
- `active_context.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core_v2/branch_punish_ranking.md`
- `heuristic_core_v2/public_info_tiers.md`
- `heuristic_core_v2/name_next_board_owner.md`
- `heuristic_core_v2/name_current_owner.md`

Triggered cards per turn listed in each turn's section.

## Turn 1

Public state: turn-1 lead RPS. p1a Jynx 100/100. p2a Zapdos 100/100.
No moves revealed.

Triggered cards loaded: `heuristic_core_v2/reset_loop_denial.md` (Rest
in package strong prior), `heuristic_core_v2/spend_or_save_piece.md`
(Zapdos = unique-role special breaker; LK Jynx threatens spending the
slot), `heuristic_core_v2/converter_before_script.md`.

### Step 1 — Candidate set (unranked)

- Thunder Wave on Jynx
- Switch Forretress
- Switch Tyranitar
- Drill Peck on Jynx
- Switch Snorlax
- Switch Raikou

### Step 2 — Per-candidate audit

| Candidate | Beats | Loses to | Dead-branch prob |
|---|---|---|---|
| Thunder Wave | LK Jynx (paras first), Ice Beam Jynx | Mean Look Jynx (locks Zapdos despite para) | LOW (Mean Look rare) |
| Switch Forretress | LK (Forry sleeps cheaply), Ice Beam (0.5x), Psychic (Steel resist) | nothing dead-into Forretress on Jynx package | LOW |
| Switch Tyranitar | Psychic (Dark blocks = 0x), Mean Look | Ice Beam (2x on Rock) | MEDIUM (Ice Beam is strong-prior, ~99% of Jynx sets) |
| Drill Peck | Stay-and-attack Jynx (chip race) | LK Jynx (Zapdos slept = sleep clause burned) | MEDIUM (LK strong-prior) |
| Switch Snorlax | Drill Peck (bulky), Ice Beam (bulky) | LK Jynx (Snorlax slept → sleep clause burned on route piece) | HIGH (LK is the threat AND Snorlax is the route piece) |
| Switch Raikou | LK (Raikou eats LK or outspeeds; Raikou Spe 115 > Jynx 95, may attack first) | Switch-in to Golem (Electric-immune wall comes in) | MEDIUM (Golem is on p1 team, revealed only if peeked; here unrevealed pre-turn-1) |

### Step 3 — Apply demotion rule

- Switch Snorlax HIGH dead-branch → cannot be top-1. Demoted out.
- Drill Peck MEDIUM (dead-into LK) → keep only if no alternative beats
  both branches. Thunder Wave beats both LK and Ice Beam. Demote.
- Switch Tyranitar MEDIUM (dead-into Ice Beam) → keep but downrank.
- Switch Raikou MEDIUM (dead-into Golem switch-in) → keep but downrank;
  note Golem is unrevealed pre-turn-1 so the demotion is lighter than
  if Golem were revealed.

### Step 4 — Revised top-3

1. Thunder Wave — LOW dead-branch; beats both strong-prior Jynx
   branches (LK + Ice Beam); preserves sleep clause AND Zapdos's
   special-breaker job (paralyzed Jynx can't LK Zapdos later either).
2. Switch Forretress — LOW dead-branch; preserves Zapdos AND sets
   Spikes pressure; Forretress absorbs LK cheaply.
3. Switch Raikou — MEDIUM dead-branch (unrevealed Golem could come in);
   preserves Zapdos AND brings a faster attacker (Raikou Spe 115 vs
   Jynx 95) who can Crunch Jynx 2x on next turn.

Demotion notes: Switch Snorlax demoted from candidates (HIGH dead-into-LK
on route piece). Drill Peck demoted from top-3 (MEDIUM dead-into-LK
plus inferior to Thunder Wave which beats the same threats). Switch
Tyranitar dropped from top-3 (MEDIUM Ice Beam, worse than Switch
Forretress for same defensive job).

### Step 5 — Cash-out justification

Not applicable. Top-1 (Thunder Wave) is not a high-variance cash-out.

### Worst plausible branch + fallback

Jynx Mean Look + Substitute trap variant locks Zapdos in. Fallback: rare
variant, accept tail risk; if it happens, sack Zapdos and bring in
Raikou-Tyranitar to break Mean Look chain via setup-into-Roar elsewhere.

### Public-info tier

Jynx LK / Ice Beam / Psychic = `strong prior`. Jynx Mean Look /
Substitute / Recover = `possible only`. p1 6-mon team = `possible only`
pre-turn-1.

---

Actual: p2 switched Zapdos → Raikou; p1 switched Jynx → Golem.

Grade:
- top_match = 0 (Switch Raikou is my revised #3, not #1)
- acceptable_match = 1 (actual is in my revised top-3 — Switch Raikou as
  preserve-Zapdos-by-faster-attacker route)
- actual_in_frozen_top_three = 1
- positive_selection = 1
- route_converting_move_chosen = 0 (switch, not converter)
- branch_punish_chosen = 0 (Thunder Wave my top-1 IS the branch
  punisher for LK, but actual route was preservation not punish; the
  branch I named Zapdos-preserves-itself wasn't promoted to #1)
- severe_blunder = 0
- hidden_info_error = 0
- state_error = 0
- mechanics_error = 0
- **top_rank_failure: route_budget** — same failure class as baseline.
  The audit-first workflow correctly DID generate Switch Raikou as a
  candidate (baseline did not generate it at all) AND placed it in
  revised top-3, but the ranking still put Thunder Wave first because
  the audit doesn't reason about preservation-vs-converter trade-offs.
  Dead-branch demotion doesn't help when no candidate is dead — the
  miss is between two LIVE candidates.

**v2 design observation (turn 1):** The intervention's audit-first
ordering caused the intervention to GENERATE switch Raikou as a
candidate (baseline only got Switch Forretress as a switch option),
and the intervention's top-3 contained the actual move. This is a
weak win (actual_in_top_3 = 1 for intervention, 0 for baseline). But
top_match unchanged. Confirms a v2 design hypothesis: probabilistic
audit gating doesn't move route_budget misses because route_budget is
a contest between live candidates, not a dead-branch demotion.
