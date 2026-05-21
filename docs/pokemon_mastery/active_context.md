# Active Context Packet

Date: 2026-05-16

Purpose: route mastery work through the small live core instead of the archive.

Hard cap: keep this file near 80-120 lines. If it grows, move details into the
archive or `heuristic_core/migration_map.md`.

## Current Objective

Become a stronger Pokemon singles advisor, using "1500 Elo" as a training
proxy. Improve unseen move choice, multi-turn re-solves, and realistic routes.
Current fix: train route-budget ranking from plausible top three to top one,
not just candidate generation or blunder removal.

Romhack AI transfer warning: vanilla GSC replay scores are training evidence
for route logic, not proof of local boss-AI correctness. Before applying a
lesson to the romhack, use `policy_cards/romhack_mechanics_firewall.md` and
`romhack_deltas/mechanics_inventory.md`. Type chart, type passives, held
items, move category, and 3-layer Spikes can invert candidates, ranges, switch
costs, and promotion; validate with local fixtures/traces before changing AI
policy.

## Startup Spine

Open first by task:

- Work-block startup: `playbook_manifest.md`, then `live_core.md`.
- Fresh unseen move choice: `live_core.md`, the public prompt, and the smallest
  useful set of tiny `heuristic_core/*.md` cards plus compact `canon/*.md` or
  `romhack_deltas/*.md` lookups only when the public board needs them.
- Scoring or progress claims: `measurement_minigoal_2026-05.md` and the
  frozen answer artifact after answers are recorded.
- Postmortem or cleanup: `heuristic_core/migration_map.md`, then the linked
  old policy card, review, quick test, ledger row, or mechanics fixture.
- Boss live advice: `live_core.md`, `boss_turn_advice_template.md`, current
  board/sheet, and only decision-relevant local mechanics status.

Do not load `cookbook.md`, `source_to_policy_ledger.md`, `paused_turn_atlas.md`,
`worked_examples/live_turn_drills.md`, long `policy_cards/*.md`, scored quick
`workspace/quick_tests/`, reviews, or raw `workspace/external_research_returns/`
before freezing fresh answers.

## Context Packets

- `live_turn`: `live_core.md`, boss template, current board/sheet, local
  mechanics status, and decision-relevant tiny heuristics if needed.
- `replay_turn_pause`: `live_core.md`, protocol, prompt, useful tiny
  heuristics, and any compact topic lookup before freezing. Keep future turns
  and answer labels hidden.
- `quick_probe_generation`: parent fresh replay miss, relevant card, and
  measurement rules. Regression only, not proof.
- `mechanics_verification`: romhack deltas, fixtures, source/debugger/emulator
  evidence, and pending index. No unverified decision mechanics.
- `study_review`: current bottleneck plus one expert source or replay. End with
  a score, fixture, policy-card update, or reject note.

## Current Measurement Snapshot

Latest plateau diagnosis: `plateau_diagnosis_001`. Working hypothesis: the
current wall is live role/package synthesis, not missing notes. Public support
reveals must update the job ledger before move ranking.

Constructed probes are nonblind regression checks, not fresh proof.

Older samples: role-package plateau flat; post-Spikes/Spin limited positive;
spectator checks regressed from exact-move noise; pre-tempo side-known flat.
See `measurement_progress_ledger.csv` for full counts and review links.

Post-tempo packet 006: 13/21 top, 20/21 acceptable, clean gates. Packets
007-017: repair loops, then 16/31 top, 29/31 acceptable. Packets 020-043:
353/681 top, 589/681 acceptable, 6 severe, 7 hidden, 6 mechanics; no proof.
Post-repair packets 032-043 are 186/361 top and 319/361 acceptable with 0
severe/hidden but 1 state/mechanics error. Packets 041-043 were 48/89 top and
72/89 acceptable after the side-known prefilter: essentially flat versus
packets 038-040, so `training_method_review_006` added branch-ranking labels.
Packet 044 tested the labels: 15/30 top, 29/30 acceptable, 25/30 actual in top
three, 27/30 actual branch named, 0 severe/hidden/mechanics, 1 state error.
Exact ranking is still flat; `training_method_review_007` and
`route_budget_tiebreaker_annotation_001` identify the next target as
route-budget tiebreaking after candidate generation succeeds.

## Compressed Live Error Families

Use `live_core.md` and relevant tiny cards rather than this section for
decisions.
The repeated old lessons are mapped in `heuristic_core/migration_map.md`.

- Owner naming: name current owner and next-board owner before choosing.
- Route-budget tiebreak: explain `#1 over #2`, when #2 becomes #1, and the
  rejected safe/default line.
- Converter ranking: promote route-changing moves above safe scripts.
- Branch punish: after naming a receiver, rank the action that beats it.
- Spend/save: preserve live route jobs; spend only for named converters.
- Reset denial: hazards, Spin, Rest, Recover, phaze, Sleep Talk, and pass
  routes count only when converted or denied in time.
- Role package ledger: screen, Charm/Pursuit, trap/perish, phaze, Spin, Curse,
  RestTalk, lure, lead item/status, pass, and cleric reveals change the job.
- Plateau loop: after a structural repair, collect 3 packets or 90 fresh side
  decisions; if flat/regressing or a miss repeats twice, study/repair first.
- Reveal re-score: Growth, Baton Pass, Substitute, Curse, RestTalk, Thief,
  lure coverage, Roar, or Whirlwind can change the whole package.
- Public tiers: preserve revealed / strong-prior / possible-only discipline.
- Romhack firewall: vanilla GSC is source material, not local truth.

## Approved Gates

Primary proof: sealed replay-transfer packets, 30-50 fresh side decisions,
target at least 55% top-match, at least 70% acceptable-match, 0 severe
blunders, at least 60% positive-selection on converter decisions, and no
repeated uncorrected error class twice in the same packet.

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

## Next Concrete Rep

Next gate: post-trade/endgame packets must use the compact freeze unchanged,
but the `Critical resource` field must contain a mini inventory:
`piece = job; piece = job; cheapest absorber = X; must-preserve = Y`.
Do this after any faint, Explosion, Spin completion, sleep/status tax, or
Leech/hazard loop. Do not claim progress unless this written inventory improves
promotion without dropping top-three coverage.

When this mini inventory is required, it must be exhaustive for the current
own side: list every remaining known own piece, including frozen, sleeping,
low-HP, or seemingly passive support. Missing a visible own piece from this
field counts as a candidate-generation failure if that piece becomes the
actual or acceptable route owner.

After the exhaustive inventory, top three must be projected from roles, not
chosen from memory: include the active converter, the named branch-cover owner,
and the cheapest absorber/preservation owner. If a slot is illegal or
irrelevant, say so inside `Critical resource`; otherwise a listed role owner
omitted from top three is a candidate-generation failure.

Active-attack variant gate: if the active Pokemon has two known serious
attacks that cover different important owners, the second attack can satisfy
the branch-cover slot. Do not omit a known active attack that covers the named
pivot just to keep a handoff-only branch-cover candidate in top three.

Support-loop broad-absorber gate: when the opponent's likely action is Leech
Seed, Reflect, phaze, status, or other low-damage support, the absorber slot is
not automatically the lowest-future-job piece. Include the healthy broad
absorber that clears seed/status pressure or stabilizes the loop if the cheap
piece is frozen, seeded, too low, or feeds recovery.

After the top three are role-filled, apply the branch-probability promotion
gate from `heuristic_core/branch_punish_ranking.md`: if a named pivot, reset
owner, spinner, phazer, or absorber is high-incentive because the opponent's
active is low, statused, passive, checked, or done with its job, that branch
owner should outrank generic active pressure unless the active-pressure move
also beats the branch or creates an immediate decisive threshold.

Rest-reset controller check: when a low/statused bulky target can Rest from
revealed or strong-prior information, or has just reset to full HP with Rest,
rank the board against the refreshed sleeper. Top three must include the
current punish, the controller for the full-HP sleep cycle, and the reset or
hazard owner. Do not overpromote a possible pivot/spin branch if the Rest
controller is the route piece that profits first.

Forced-reset handoff check: if active damage, status, or phaze pressure can
only trigger Rest, Recover, Spin, or another reset without preventing it,
include the owner of the post-reset board before repeating the active move.
Attack stays #1 only when it KOs, blocks the reset, or leaves a better forced
state after the reset than the handoff would.

Own-sleeper tempo check: when our sleeping RestTalker or sleeper can enter or
stay on an opposing asleep, passive, or low-threat target, include that
sleep-burn line as a controller candidate, not an automatic #1. It preserves
unique route pieces while turning the sleep counter into future Surf, Spin,
Sleep Talk, Rest, or absorber value. Promote it only when the opponent's
immediate route is truly passive; keep active breakers, phazers, status moves,
or setup controllers above it when those actions must happen before setup,
Reflect, Toxic, Spin, or a forced threshold converts.

Finish-job versus preserve-owner check: if a finite-job piece is likely to die
before another clean turn, promote the move that completes its job now. If the
active move is only a possible lure or low-certainty punish, preserve the
revealed-pressure owner instead.

Already-statused absorber check: when revealed or strong-prior sleep, Toxic,
paralysis, or status is the branch, include the already statused/asleep piece
that can absorb it while preserving fresh route owners. Promote it only if it
survives revealed damage well enough or has lower remaining job value than the
fresh phazer, cleaner, support, or converter it protects.

Support cash-out check: if that same support/status user has revealed or
strong-prior Explosion, Self-Destruct, Destiny Bond, or another cash-out, price
the low/statused sack before spending a fresh status/phaze owner. Status first
is top only when it acts before cash-out and losing the owner is acceptable or
route-winning.

Support-lane legality gate: before a support move can outrank cash-out, verify
the public state says it still changes something. Do not promote Spikes when
that side already has Spikes, Toxic/status into an already statused or immune
target, Spin when no hazards are present, or phaze/status that does not change
the next route.

Compressed-endgame reledger: after cash-out, multiple faints, or a forced
low-support entry, top three must include active converter/finish-job,
controlled sack or stay-in if the active has the lowest future job, a
lowest-future-job bench sack when it creates clean owner entry, and the
defensive owner for the opponent's highest-incentive next attacker or pivot.
Do not let a narrow active job hide the next defensive owner.

Handoff triad check: when a switch or preserve/spend handoff is plausible,
class every listed own piece that can enter or stay as one of three roles
before ranking: direct absorber, route converter/status owner, or cheapest
scout/sack. Top three must include the best legal member of each live role
unless the role is impossible or strictly dominated. Promote the direct
absorber only after comparing it to the route converter and the cheapest
scout/sack; a piece named in `Critical resource` but omitted from this triad is
a candidate-generation failure if it becomes the actual or acceptable owner.

Support-owner lane: do not let the direct absorber hide a support converter.
If another piece survives the revealed or strong-prior hit well enough to spend
Toxic, Spikes, Spin, phaze, Protect, sleep/status absorption, or cash-out, list
it as the route converter/status owner lane before the passive wall. It outranks
the wall when the wall only absorbs and the support move changes the next turn.

Top-three candidate slot contract: before ranking a preserve/spend board, fill
the live slots if legal: active first-action converter/cash-out that moves
before being removed, support/offensive route owner that changes the next turn,
and stable absorber/preservation owner. Keep the risky active converter in top
three before demoting it; keep the support owner separate from the passive wall.

Target-specific handoff scoring: do not rank generic "Baton Pass" or "switch"
when targets differ. Name the target and price immediate conversion, entry
cost, boost usefulness, status/hazard exposure, and next owner. A handoff target
with a unique immediate route job must appear by name in top three.

Doomed-target sink lane: a low/statused/dead-on-reentry target is still a legal
handoff target if it absorbs Screech, Toxic, Thunder Wave, phaze, scout damage,
or another non-damaging branch that would cripple the true owner. Name it in top
three when its death or status preserves the actual route piece.

Handoff target matrix: on any switch, pass, sack, or preserve/spend turn, turn
the resource ledger into target -> first forced action -> route gained/protected
before ranking. Include live lanes for active move, support converter,
low/statused or sleeping sink, wake-eligible/off-field route owner, and stable
support sink. Top three must be selected from this matrix.

Cash-out candidate census: on any active Explosion, Self-Destruct, Destiny
Bond, or low-piece irreversible-status turn, write a compact census before
top-three compression: active reversible/setup/support, active irreversible,
direct absorber, route owner, and branch-immune or low-job pivot. Top three
must be selected from this census, and any omitted live job needs a dominance
reason in `Critical resource`. Cycle 74 moved candidate inclusion from 7/10 to
9/9; use this as the default candidate-generation method before promotion.

Lane-tagged top three: on handoff turns, each ranked candidate must include its
matrix lane in brackets. If a live unique lane is omitted, write why it is
dominated before reveal.

Must-cover lane gate: do not choose top three first and label them afterward.
Inside `Critical resource`, start handoff turns with `Must-cover lanes:` and
copy those lanes into top three. If more than three lanes are live, write
`Excluded live lane:` with the target and the concrete dominance reason before
reveal. A sleeping/off-field route owner, low/statused sink, or stable support
sink named in the ledger is not optional just because it is passive.

Setup lane in must-cover gate: when Curse, Growth, Belly Drum, or repeated
boosting competes with Rest, attack, phaze, or switch, `Must-cover lanes:` must
include active setup as its own lane if the user survives to move and the boost
changes a damage, Rest, parity, or phaze threshold. Do not collapse setup into
active damage or preservation.

Sleep-action0 class check: when a prompt says `Rest sleep actions 0`, classify
it before ranking. If the Pokemon just used Rest, Sleep Talk is expected. If
action0 follows two prior sleep actions, a switch-out, or Sleep Talk calling
Rest, treat it as wake-eligible and rank the awake converter normally.

Setup-race timing ledger: when Curse/Growth/Drum-style setup competes with
attack, Rest, phaze, or handoff, use
`heuristic_core/setup_race_timing.md`. Before promotion, name boosts, HP after
Leftovers, last observed damage, Rest/wake turn, phaze certainty, and the next
threshold changed. Continue setup when damage does not force Rest/KO before
parity; attack only when it creates the threshold; switch only when the
wall/phazer is confirmed enough or staying loses the setup route.

Clean-entry sack promotion: within the handoff triad, the cheapest scout/sack
outranks the direct absorber when it covers the opponent's highest-incentive
attack, phaze, or setup turn and creates a clean entry for the converter that
would otherwise take Spikes plus the hit or be Roared before acting. Keep the
direct absorber first only when it converts before that branch acts or the sack
does not actually produce a better entry board.

Pivot-reset candidate pass: after the opponent switches, phazes, or reveals the
actual attacking branch, rebuild top three from the new active target before
continuing the old route. Include the best current active move into that
target, the direct absorber, and the lowest-job absorber/sack that handles the
new target's highest-incentive action. The previous route owner stays top only
if it still beats this new target or denies its reset/pass/setup branch now.

Protect-cycle exact-range ledger: in a low-piece endgame with Protect,
Leftovers, poison, sleep turns, or repeated damage, do not call a move exact
until the freeze states last observed damage, current HP after recovery, and
the post-Protect HP if this turn is blocked. Rank accurate damage above
higher-power miss risk when both create the same two-turn route. Rank status or
setup above damage when damage is not exact and the target's next action KOs,
resets, or Protect-cycles out of range.
