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
Claim only catastrophic-error improvement until hidden/state/mechanics errors
decline too.

Keep constructed probes separate from fresh replay evidence; they are nonblind
regression checks, not proof.

Latest fresh transfer: `cashout_immunity_transfer_001`: 15/30 top, 19/30 acceptable, 0 severe/hidden, 24/30 positive, 12/21 route, 10/18 branch.
Not broad progress; cash-out guard held in a limited sample, but top/acceptable remain below gate.

## Active Error Classes

- Sleep source and absorber assignment: do not assume the revealed sleeper is
  always the future sleep source. Track sleep by side; if the opponent has not
  slept one of ours, name the absorber before choosing damage.
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
  Defending mirror: before attacking a low self-KO candidate, name speed/order,
  survival, and the defensive owner. Rest race: if a faster low target can heal
  before the hit, attacking may cash out into a preserved target.
- Branch-action after naming: name the next-board owner, then choose the
  handoff, coverage, setup/Substitute, phaze, or utility move that beats it.
  For sleep/status absorbers, rank absorber-punish before status. If a sleeping
  RestTalk piece can re-enter, price that switch. Before Explosion/all-in
  cash-out, name revealed and plausible hidden immunity owners. Use
  `policy_cards/branch_action_after_naming.md`.
- Safe but non-converting lines: 0 severe is only a gate. Fresh work must score
  positive selection: route-converting move, branch punish, and top-3 ranking.
- Hazard-loop Spin window: price whether the spinner's current job is Spikes,
  Spin, Explosion, or pivot before sending the spinblocker. If the spinner is
  status-controlled and the setter has a future job, hand off to pressure.
  Before Spin, ask whether the active setter can place missing Spikes on the
  opponent's side; after Spin, ask whether the opposing setter can reset Spikes.
  If a boosted threat is already converting, status/phaze/cash-out can outrank
  both Spikes and Spin.
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
blunders, at least 60% positive-selection on converter decisions, and no
repeated uncorrected error class twice in the same packet. Thresholds are
provisional.

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

Default: main-agent-led specialist bursts for separable work only. No output
becomes policy until mapped to trigger/default/exceptions/worst branch/status/drill.

## Next Concrete Rep

Fresh positive-selection transfer: when a status-capable Pokemon faces an
obvious receiver, rank item removal, coverage, handoff, setup/phaze, and status
before choosing.
