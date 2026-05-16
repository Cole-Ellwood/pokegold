# /pgoal Packet Protocol — durable template for packets 046+

The /pgoal armed 2026-05-16 needs ≥5 cross-replay lifts + ≥2
consecutive cross-packet lifts + same-replay counterfactual control.
Each packet runs ONE fresh tournament replay through BOTH the baseline
arm and the intervention arm, freezing per-turn before peeking actuals.

This file is the durable protocol. Per-packet variation lives in
`workspace/pgoal_<NNN>_inputs.md` (replay URL + side) and
`workspace/quick_tests/pgoal_<NNN>_<arm>_<replay>_<date>.md` (the
two arm artifacts).

## Per-packet inputs

Before running, write `workspace/pgoal_<NNN>_inputs.md`:

```
# pgoal Packet <NNN> Inputs
replay_url: <full URL, e.g. https://replay.pokemonshowdown.com/smogtours-gen2ou-NNNNNN>
replay_id: <short id, e.g. smogtours-gen2ou-NNNNNN>
side: <p1|p2>
side_known_source: <one line describing where the team came from>
reconstruction_peek_turns: <comma-sep turns peeked at for team reconstruction, or "none">
chosen_at: <YYYY-MM-DD>
```

Replay selection rules:

- Must be a Smogon Showdown / Smogon Tours GSC OU tournament replay.
- Must NOT be referenced anywhere in `docs/pokemon_mastery/` already
  (verify with `grep -r "<replay-id>" docs/pokemon_mastery/` returns
  zero hits).
- Must run past turn 30 of meaningful battle state.
- Side selection: pick the side whose 6 sets you can fully reconstruct
  from a public source (Smogon search API, paste sheet, or by inspecting
  later turns of the replay log for SPECIES ONLY — never moves, items,
  or post-turn-N outcomes).
- Record the reconstruction peek turns honestly. If you peeked turns
  1-30 to build the team list, write "1-30 (species only)". This is the
  contamination caveat the audit needs to evaluate.

## Per-turn dual-freeze workflow

Each turn produces TWO frozen answers — one per arm — both before any
actual reveal. The single-session contamination risk (writing baseline
first biases the intervention answer) is mitigated by the v2 artifact's
forced audit-first ordering: the intervention's structural workflow
demands a fresh candidate set before ranking, so anchoring on the
baseline pick is detectable in the artifact (the audit step would
match-rationalize).

Per turn N:

1. Reveal log only up to turn N's pre-decision state. Use:
   `python tools/pokemon_mastery/replay_turn_pause.py <log> prompt --turn N`

2. **Baseline arm freeze**. Load:
   - `live_core.md` (NOT v2)
   - `active_context.md`, `replay_turn_pause_protocol.md`
   - `heuristic_core/branch_punish_ranking.md`,
     `heuristic_core/public_info_tiers.md`,
     `heuristic_core/name_next_board_owner.md`,
     `heuristic_core/name_current_owner.md`
   - Any `heuristic_core/*.md` triggered by Load-Required Triggers in
     `live_core.md`.

   Then freeze a baseline answer per the v1 artifact format:
   - Pre-freeze loaded cards (list every card name)
   - Recommended move, confidence, route reason
   - Top three with one-sentence each
   - Serious alternatives, rejected safe line, worst plausible branch
   - Public-info tier
   - Branch-punish audit per top-3 (the audit-text-after-rank format)

3. **Intervention arm freeze**. Load:
   - `live_core_v2.md` (NOT v1)
   - `active_context.md`, `replay_turn_pause_protocol.md`
   - `heuristic_core_v2/branch_punish_ranking.md`,
     `heuristic_core_v2/public_info_tiers.md`,
     `heuristic_core_v2/name_next_board_owner.md`,
     `heuristic_core_v2/name_current_owner.md`
   - Any `heuristic_core_v2/*.md` triggered by Load-Required Triggers
     in `live_core_v2.md`.

   Then freeze an intervention answer per the v2 audit-first artifact
   format (Steps 1-5 in `live_core_v2.md`):
   - Pre-freeze loaded cards
   - Step 1: candidate set (3-5 unranked)
   - Step 2: per-candidate audit table (beats / loses-to / probability
     tag HIGH/MEDIUM/LOW)
   - Step 3: demotion notes
   - Step 4: revised ranked top-3
   - Step 5: cash-out justification (when applicable)
   - Worst plausible branch + fallback
   - Public-info tier

   The intervention answer must NOT just match-rationalize the baseline
   pick. If the audit yields a different top-1 vs the baseline arm,
   record the divergence as a Step 4 note.

4. **Reveal actual**:
   `python tools/pokemon_mastery/replay_turn_pause.py <log> reveal --turn N`

5. **Score both arms** independently against the actual move. Score
   tags per `replay_turn_pause_protocol.md` §Scoring.

6. Continue to turn N+1 until 30 scored decisions or protocol
   §Exclusions / §When-To-Stop triggers.

## Output artifacts

Write two artifacts, one per arm, at:

```
docs/pokemon_mastery/workspace/quick_tests/pgoal_<NNN>_baseline_<replay-id>_<date>.md
docs/pokemon_mastery/workspace/quick_tests/pgoal_<NNN>_intervention_<replay-id>_<date>.md
```

Each artifact follows the score summary template from
`replay_turn_pause_protocol.md` §Artifact Template, plus the per-turn
freeze record for that arm.

## Ledger rows

Append TWO rows to
`docs/pokemon_mastery/measurement_progress_ledger.csv`, one per arm.
The `run_id` field MUST follow exactly:

```
pgoal_<NNN>_baseline_<replay-id>_<date>
pgoal_<NNN>_intervention_<replay-id>_<date>
```

Example:

```
pgoal_046_baseline_smogtours-gen2ou-936068_2026-05-16
pgoal_046_intervention_smogtours-gen2ou-936068_2026-05-16
```

The verifier `tools/mastery/check_proof_bar.py` REQUIRES this exact
format to detect arm + packet number. Any other format is treated as
legacy and ignored by proof-bar checks.

Other required ledger fields (per existing schema):

- `date_utc`: YYYY-MM-DD
- `test_type`: `pgoal_replay_dual_arm` (new tag for /pgoal packets)
- `pool`: `<replay-id>_turns_1_NN_<side>_<arm>`
- `scenario_count`: number of scored decisions
- `top_move_agreement`: `<top>/30` form
- `acceptable_move_agreement`: `<acceptable>/30` form
- `severe_blunders`, `state_errors`, `hidden_info_errors`,
  `mechanics_errors`: integers
- Other agreement fields per existing rows

## Pass / fail per packet

For a single packet, the SAME-replay arm comparison is the unit of
analysis:

- **Lift**: intervention top-match - baseline top-match >= 3.
- **Flat**: |delta| <= 2.
- **Regression**: intervention < baseline by >= 3 (intervention
  actively harms; document why).

A single packet's lift is necessary but not sufficient evidence. Proof
bar needs ≥5 lifted packets (one per replay) and ≥2 consecutive lifted
packets, plus baseline arm mean staying near plateau (verifier C3).

## Honesty rules (no peeking)

- Do NOT read forward turns of the replay for anything except SPECIES
  reconstruction (and record the peek turns in the inputs file).
- Do NOT read the actual move for turn N before BOTH arms' freezes
  are written.
- Do NOT load v2 cards while writing the baseline arm freeze, or v1
  cards while writing the intervention arm freeze. The card-loading
  discipline is the counterfactual.
- Do NOT edit `heuristic_core/` or `live_core.md` in any iteration of
  /pgoal. Baseline is frozen at fad81f02. Edits go only in v2 paths.
- Do NOT promote a single miss into a new card rule. New cards only when
  a specific miss has zero rule encoding the right answer (H3 mode), and
  only after the miss repeats across packets.

## Diagnosis output (when applicable)

If after packets 046-050 the proof bar does not pass, write
`docs/pokemon_mastery/reviews/proof_bar_diagnosis.md` with:

- Per-packet lift table (arm deltas across all 5 replays).
- Failure-mode breakdown (H1/H2/H3/H4 across all misses).
- The specific mechanism that prevents lift, with evidence.
- What would need to change (multi-oracle pivot, decision-tree cards,
  different model, etc.) and estimated cost.

The diagnosis is a valid proof-bar completion path per the original
goal: "Prove the training loop generalizably moves top-match OR sharply
diagnose why it cannot, naming the exact mechanism."

## Replay sourcing

Replay URLs come from:

- Smogon Tours GSC OU brackets (live tournament archive)
- Smogon GSC OU sample replays page
- SPL / WCOP / classic team tournament archives

If autonomous fetch is needed during /pgoal:

```
curl -fsSL https://replay.pokemonshowdown.com/<replay-id>.log -o <local-path>
```

Smogtours equivalent:

```
curl -fsSL https://replay.pokemonshowdown.com/smogtours-gen2ou-<id>.log -o <local-path>
```

If both fail and no candidate is forthcoming, BLOCK the loop with
`<pgoal-blocked>` rather than silently picking an unsuitable replay.

## Already-used replay registry

These replays are referenced in `docs/pokemon_mastery/` and must NOT
be picked for fresh /pgoal packets (verify with grep before commit):

- smogtours-gen2ou-781283 (packet 045 Claude run)
- smogtours-gen2ou-936068 (packet 045 Codex run)
- smogtours-gen2ou-821941 (packet 044)
- smogtours-gen2ou-912287 (branch_absorber probe)
- smogtours-gen2ou-912827 (cashout_immunity probe)

Add to this list as packets consume new replays. The grep before commit
is the canonical check; this list is a hint, not the truth.
