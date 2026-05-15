# Active Context Packet

Date: 2026-05-14

Purpose: keep future Pokemon mastery work inside a small, current context
packet. This file is not a replacement for the archive. It tells the next work
block what to load first, what to avoid loading by default, and what evidence
currently matters.

Hard cap: keep this file near 100-150 lines. If it grows, move details into a
policy card, quick-test artifact, mechanics fixture, or review.

## Current Objective

Become a measurably stronger Pokemon singles advisor, using "1500 Elo" as a
training proxy rather than proof. The live target is better unseen move choice:
plan multiple turns ahead, re-solve after new information, and preserve or
improve realistic win routes.

Pokemon Showdown ladder ratings are only proxies. PS documents Elo, GXE, and
Glicko-1 separately and says there is no official universal Elo standard.

## Startup Spine

Open these before making broad claims:

- `master_index.md`
- `active_goal.md`
- `training_cycle.md`
- `measurement_minigoal_2026-05.md`
- `replay_turn_pause_protocol.md`
- `boss_turn_advice_template.md` for live advice
- this file
- 1-3 relevant `policy_cards/*.md`

Do not load `cookbook.md`, `source_to_policy_ledger.md`, or large research
returns in full unless the selected rep needs them.

## Context Packets

- `live_turn`: boss template, current board/sheet, one card, local mechanics
  status, last active error. Stop if missing state is the blocker.
- `replay_turn_pause`: protocol, measurement minigoal, prompt, and relevant
  card after freezing. Keep future turns and answer labels hidden.
- `quick_probe_generation`: parent fresh replay miss, relevant card, and
  measurement rules. Regression only, not proof.
- `mechanics_verification`: romhack deltas, fixtures, source/debugger/emulator
  evidence, and pending index. No unverified decision mechanics.
- `study_review`: current bottleneck plus one expert source or replay. End with
  a score, fixture, policy-card update, or reject note.

## Current Measurement Snapshot

Latest measurement read: severe blunders improved, but total errors did not.
First 20 fresh rows had 5 severe and 2 state errors; latest 20 had 1 severe, 3
state, 4 hidden-info, and 1 mechanics error. Claim only
catastrophic-error improvement until hidden/state/mechanics errors decline too.

Constructed probes mostly pass 4/4 or 5/5; latest
`screen_phaze_third_owner_probe_001` 4/4. Keep them separate from fresh replay
evidence because they are nonblind regression checks.

Latest fresh transfer:
`replay_turn_pause_078` 10/30 top-match, 18/30 acceptable-match, 0 severe
blunders. It stopped after repeated branch-action misses: I named Raikou and
Skarmory receivers, then clicked active pressure instead of counter-switching.
It also missed low Cloyster Explosion into the incoming Tentacruel.

Latest focused transfer: `setup_hidden_role_stop_transfer_001` on
`smogtours-gen2ou-921412` scored 16/39 top, 25/39 acceptable, 0 severe, and 0
mechanics/state/hidden-info errors. It improved phaze/support recognition but
missed exact handoffs, Reflect+Roar, third-owner Misdreavus, and low no-Rest setup.

## Active Error Classes

- Sleep source and absorber assignment: do not assume the revealed sleeper is
  always the future sleep source. A Pokemon put to sleep is commonly switched
  out and saved for Sleep Clause value, but that is a tendency, not a script.
- Rest sleeper handoff: a Rested or otherwise sleeping route piece may stay to
  burn a safe sleep turn, use Sleep Talk, or switch out and be saved while
  another piece meets the counter-pivot. Name the next board before choosing.
  If the opponent moves before the Rest wake event, do not status the still
  sleeping target by habit.
- Snorlax set ambiguity: price Lovely Kiss, RestTalk, Curse, phazing support,
  and recoil/damage before choosing the absorber or response.
- Voluntary-entry intent: raise the prior on hidden coverage/lure/cash-out when
  a piece enters a bad-looking matchup, but keep fact tiers explicit: revealed,
  strong prior, or possible only. Possible-only moves cannot anchor the main
  recommendation. Use `policy_cards/hidden_role_voluntary_entry.md`.
- Active pressure versus status script: do not turn every status-capable
  Pokemon into Hypnosis, Sleep Powder, or Toxic. Price direct damage, forced
  switches, and phazing first when those already improve the route. Use
  `policy_cards/active_pressure_before_status.md` when this is the bottleneck.
- Cash-out before status script: if a one-time support piece can remove the
  active route converter now, price Explosion/sacrifice before sleep or status.
- Branch-action after naming: naming the opponent's likely switch, absorber, or
  support branch is not enough. If that branch is best, choose the counter-
  switch, coverage, setup, phaze, or utility move that beats it. Use
  `policy_cards/branch_action_after_naming.md` when this is the bottleneck.
- Hazard-loop Spin window: Spikes progress only matters if the route retains,
  punishes, removes, or converts the hazard state. Price whether the spinner's
  current job is reciprocal Spikes, Spin, Explosion, or pivot before sending the
  spinblocker. If the spinner is already status-controlled and the setter still
  has a future job, hand off to pressure before resetting hazards or cashing out
  by habit.
- Phaze-loop commitment: when a healthy phazer plus Spikes is already
  converting, do not abandon the loop until the opponent shows an entry path
  that removes hazards, forces damage, lands status, or creates a better
  counter-pivot.
- Low-support preservation versus immediate cash-out: preserve a weak support
  piece when it still has a route job; spend it when a concrete converter opens.
  Low RestTalk Zapdos and healthy Gengar both count as route pieces when they
  still preserve the hazard or pivot map.
- Support handoff: after a support job lands, identify the next board and the
  counter-pivot before assuming the job is complete.
- Romhack mechanics firewall: vanilla GSC knowledge is source material, not
  local truth.

## Approved Gates

Primary proof: sealed replay-transfer packets, 30-50 fresh side decisions,
target at least 55% top-match, at least 70% acceptable-match, 0 severe
blunders, and no repeated uncorrected error class twice in the same packet.
Thresholds are provisional.

Secondary proof: targeted regression probes. Use at most one small constructed
probe per fresh replay miss by default, split only separate boundaries, and
never count artifact volume as progress.

## Web Search And Local-Only Triggers

Use web search when selecting fresh Smogon/GSC material, checking current
competitive sources, extracting a new source-to-policy rule, verifying current
Showdown rating docs, or investigating a repeated error not explained locally.

Do not web search before freezing a sealed answer. Do not use web search to
settle romhack mechanics that require local docs, source, fixtures, debugger
output, or emulator traces.

## Subagent Rules

Default: main-agent-led specialist bursts for separable work only. Each packet
needs objective, allowed sources, forbidden info, output schema, stop condition,
and max references; no output becomes policy until mapped to trigger, default,
exceptions, worst branch, local status, and drill.

## Next Concrete Rep

Fresh transfer: screen-plus-phaze and third-owner loop re-score - Reflect+Roar,
Misdreavus third owner, low setup without hidden Rest import, active damage.
