# Pokemon Mastery Study Roadmap - 2026-05-14

Purpose: make the next Pokemon study work measurable and useful for actual
move choice. This is not a general documentation beautification plan.

## North Star

Become better at no-Team-Preview GSC / Pokemon Gold romhack battle decisions:
name the route, price hidden information honestly, preserve the right resource,
choose a move, and revise the plan after new evidence.

## Roadmap Priorities

### 0. Immediate Next Reps Queue

This queue outranks broad organization.

| Priority | Rep | Output |
| ---: | --- | --- |
| 1 | Turn-pause one unseen Smogon GSC tournament replay | scored replay run plus error-class notes |
| 2 | Quick Test 001 with 10 fresh or semi-blind scenarios | `measurement_progress_ledger.csv` row plus error-class notes |
| 3 | One filled Pryce recorded-attempt worksheet | `worked_examples/pryce_scored_manual_worksheet.md` filled from real capture |
| 4 | Spikes / Rapid Spin fixture completion | updated `mechanics_fixtures/spikes_rapid_spin/README.md` |
| 5 | One adaptive opener trace and one fixed opener trace | route-map confidence update |
| 6 | One type/passive fixture from the priority list | updated `romhack_deltas/type_passive_fixture_priorities.md` |
| 7 | Five hidden-info atlas entries converted into public prompts | new PTA/live-turn drills with sealed answer separation |
| 8 | One cross-domain transfer sprint if a repeated error appears | STP/PTA/helper/reject note tied to a Pokemon score |

### 1. Measurement Before More Notes

Current docs already contain enough material to study. The bottleneck is proof
that advice quality is improving.

Deliverables:

- Run a 10-question quick probe using `measurement_minigoal_2026-05.md`.
- Record it in `measurement_progress_ledger.csv`.
- Keep exact hidden answers out of visible study docs until after scoring.
- Track error classes: mechanics, public-state omission, route error,
  hidden-info overclaim, severe blunder, stale-plan continuation.

Success signal:

- Scores improve across repeated semi-blind probes, and severe blunders shrink.
- Replay turn-pause disagreement analysis produces fewer repeated route errors
  across unseen games.

### 2. Real Boss Attempt Evidence

The 50-battle validation gate is not ready until real capture evidence exists.

Deliverables:

- Use `workspace/battle_captures/README.md` and
  `worked_examples/pryce_recorded_attempt_capture_protocol.md` for the first
  recorded boss attempt.
- Fill `worked_examples/pryce_scored_manual_worksheet.md`.
- Extract only the reusable mistake classes into the cookbook or ledger.

Success signal:

- The advice can be graded before the outcome is known.

### 3. Romhack Mechanics Verification

Local source and fixtures must outrank vanilla memory.

Deliverables:

- Finish the pending Spikes / Rapid Spin fixture items in
  `mechanics_fixtures/spikes_rapid_spin/README.md`.
- Prioritize local type/passive checks from
  `romhack_deltas/type_passive_fixture_priorities.md`.
- Verify phazing, last-mon behavior, Foresight/immunity interactions, Focus
  Band, Quick Claw, Mirror Coat, Counter, Encore, and Sleep Talk/Rest where
  route advice depends on them.

Success signal:

- Boss advice stops saying "probably" about mechanics that can be locally
  tested.

### 4. Hidden-Information Training

No Team Preview is central. Early turns should preserve optionality rather than
pretend the unseen team is known.

Deliverables:

- Convert selected entries from
  `workspace/external_research_returns/2026-05-14_deep_research_hidden_info_turn_atlas.md`
  into paused-turn drills.
- Add Bayesian/non-reveal examples for Rapid Spin, hidden coverage, priority,
  and repeated switch routes.
- Keep sealed hidden state out of the public prompt.

Success signal:

- The answer distinguishes likely, possible-only, disproven, and impossible
  after four revealed moves.

### 5. Boss AI Cheap-Win Audit

The best AI work is small, public-information-only, and traceable.

Candidate audits:

- Four-move saturation hard gate.
- No-progress move-loop counter.
- Safe-finish clamp.
- Hazard retention against active/revealed/legal-prior spinners.
- Robust progress over possible-only counterplay.
- Opportunity-weighted non-reveal downgrade.
- Observed speed-order memory, with the approved exact-speed exception kept
  separate.

Success signal:

- Each accepted AI change has an audit fixture and trace fields before coding.

### 6. Simulator And Tooling Stance

Default answer: do not build a full battle simulator yet. The project already
has enough simulator-adjacent pieces for the current stage:

- Pokemon Showdown exists for vanilla battle simulation and replay practice.
- `poke-env` exists for Python agents on top of Showdown.
- The repo already has local damage/debugger, hazard smoke, boss AI trace,
  preference fixtures, and audit tooling.

Use each tool for the job it can actually prove:

| Tooling path | Use now | Do not use for |
| --- | --- | --- |
| Pokemon Showdown | Vanilla GSC practice, replay study, rough transfer baselines. | Romhack mechanics truth. |
| `poke-env` | Vanilla or transfer agent baselines on Showdown. | Counted Gym Leader Lab proof. |
| Local debugger / emulator fixtures | Romhack mechanics truth: damage, passives, hazards, move timing. | Broad strategic win-rate claims by itself. |
| Boss AI trace tools | Public-state AI behavior audits and cheap no-cheat policy checks. | Player-side mastery proof without battle outcomes. |
| Manual recorded boss attempts | Bridge from study notes to automation. | Large aggregate claims until capture/scoring is routine. |

Build small harnesses before any end-to-end simulator:

- Quick Test runner for 10-scenario semi-blind probes.
- Turn-pause replay helper that reveals one unseen log turn at a time and
  hides future actions.
- Practice selector that samples drills by failure mode and last-practiced date.
- Mechanics-pending index from `verify` / `unverified` lines.
- External hidden-info atlas splitter that separates public prompt from sealed
  hidden state.
- Small uncounted boss-run harness only after one real captured attempt, one
  declared player team/ruleset, and key mechanics blockers are closed.

Success signal:

- Tooling reduces hidden-info mistakes, mechanics mistakes, or severe blunders
  in scored probes. If it only produces infrastructure, stop.

### 6.5 Autonomy And Transfer Sprints

Full autonomy is part of the method. I should use it when Pokemon-only reps are
not attacking the current bottleneck.

Allowed high-variance work:

- study poker AI / imperfect-information game solving for no-Team-Preview
  belief states, mixed strategy, and subgame re-solving;
- study chess, Go, shogi, RTS, fighting games, or sports analytics for
  conversion, sacrifice timing, option coverage, and risk calibration;
- build small helper programs that reduce contamination or expose decision
  errors;
- run external simulations or baselines when the result can be checked against
  local mechanics limits.

Success signal:

- the tangent produces a Pokemon artifact: source-to-policy entry, paused-turn
  drill, quick-test canary, boss-AI audit, fixture, helper, or explicit reject
  note;
- a later replay/probe shows fewer errors in the targeted class.

### 7. Source Mining Queue

Use web sources when they answer a training gap, not because the docs need more
volume.

High-priority GSC sources to mine or re-mine:

- Smogon Gold/Silver competitive resource hub:
  https://www.smogon.com/resources/competitive/gs/
- Jorgen, Playing with Spikes in GSC:
  https://www.smogon.com/gs/articles/gsc_spikes
- Jorgen, Explosion in GSC:
  https://www.smogon.com/gs/articles/guide_to_explosion
- Oglemi / havoc / Earthworm, Introduction to Status in GSC:
  https://www.smogon.com/resources/competitive/gs/status
- Siatam, GSC OU Sample Teams Breakdown:
  https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/

Why these remain useful:

- The resource hub points to mechanics guides, status, move priority, OU speed
  tiers, and Spikes.
- The Spikes guide gives concrete spin, spinblock, Toxic, Icy Wind, and
  baiting lines, while warning that vanilla GSC has one Spikes layer. The
  romhack has its own three-layer fork, so transfer must be explicit.
- The Explosion guide frames Explosion as offensive, defensive, and tactical
  route conversion rather than generic damage.
- The Status article is still a useful guard against later-gen status and
  Sleep Talk assumptions.
- The sample teams thread ties teams to threat checks, wall breaking, synergy,
  and replays; this is ideal for route-map and no-preview practice.

### 8. Roadmap Ideas To Reject For Now

- A giant rewrite of every doc.
- Deleting reviews because their lessons also appear in the cookbook.
- Building a large simulator before Quick Test 001, the first real captured
  boss attempt, and the key mechanics fixtures.
- Optimizing folder aesthetics without improving retrieval or scoring.
- Treating external research outputs as automatically correct.
- Creating more route sheets before testing existing route sheets in live
  advice.

## Creative But Actually Useful Ideas

1. Build a small practice selector that samples unseen or stale drills by tag.
   It should choose from existing docs; it should not generate answers.
2. Create a `mechanics_pending` index from all "verify" lines in boss route
   maps and worked examples.
3. Convert the Deep Research JSONL block into a practice-prompt index with
   public prompt separated from sealed hidden state.
4. Add a "last practiced" column to drills only after quick probes are running.
5. Build a local search alias for live advice, e.g. hazards/spin/sleep/status
   route queries across `cookbook.md`, `worked_examples/`, and `romhack_deltas/`.
6. Add a tiny simulator-readiness command that reports whether the 50-battle
   gate is blocked by missing team/ruleset, mechanics, capture, or opponent
   model evidence. This should summarize existing docs, not invent confidence.
7. Run a poker-AI transfer sprint focused on exploitability and subgame
   re-solving after two repeated hidden-info or prediction errors.

## Coverage Labels To Add Gradually

Do not rewrite old docs just to add labels. Add these when a file is already
being touched:

- `public_practice`
- `semi_blind`
- `sealed`
- `source_grounded`
- `runtime_verified`
- `romhack_unverified`
- `boss_ai_public_only`
- `player_advice_source_known`

## Next 10 Hours

| Time | Work | Output |
| ---: | --- | --- |
| 1h | Run and score a 10-question quick probe | New row(s) in `measurement_progress_ledger.csv` |
| 1h | Turn-pause an unseen Smogon GSC replay | Scored replay run with error classes |
| 2h | Convert 5 hidden-info atlas entries into drills | New PTA or live-turn prompts |
| 2h | Finish one mechanics fixture family | Updated `mechanics_fixtures/` and `romhack_deltas/` |
| 2h | Review one unseen long GSC battle | One review plus STP/PTA extraction |
| 1h | Score a real or reconstructed boss attempt | Filled worksheet |
| 1h | Audit one cheap boss-AI proposal against source | Accept/reject note with fixture need |
| 1h | Cross-domain transfer sprint if a repeated error is active | STP/PTA/helper/reject note |
| 1h | Update indexes only for new artifacts | No broad rewrite |

## Progress Kill Switch

Stop organizing and resume battle study when any of these are true:

- No new scored probe has been run in the last study block.
- The edit does not make a future live-turn answer faster, safer, or more
  measurable.
- The work is only making docs prettier.
- The same strategic lesson is being rewritten for the third time without a
  new test, fixture, or battle position.
