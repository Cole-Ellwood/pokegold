# One-Cycle Converter Check 001 - smogtours-gen2ou-927016 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-927016`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-927016.log`

Selection metadata:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=8`

Mode: focused spectator-public no-Team-Preview check after
`post_spin_branch_replication_transfer_001`. The target was one-cycle
converter staging: Curse, coverage, phaze, Explosion, Rest, and owner handoff.

Contamination control:
- Local `rg` found no prior `smogtours-gen2ou-927016` references in `docs` or
  `tmp` before download.
- No replay UI, team paste, or future turns were inspected pre-freeze.
- The log was exposed only through prompt/reveal for turns 1-9.
- Post-score web study used Smogon GSC sources after answers froze.

Post-score web/current sources:
- Smogon Forums, [GSC OU Steelix](https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/).
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).
- Smogon, [Introduction to Competitive GSC](https://www.smogon.com/smog/issue28/gsc).
- Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion).

## Score Summary

Decisions: 17 scored, with turn 5 p2 unscored because full paralysis hid the
chosen move.

Top-match: 4/17.

Acceptable-match: 14/17.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 12/17.

Route-converting move chosen: 9/17.

Branch-punish chosen: 8/16.

Role-package update obeyed: 9/14.

Earliest meaningful error: turn 2, missed the Raikou owner handoff in the
Cloyster mirror. The targeted structural error appeared turns 6-9: I priced
cash-out but did not stage support delivery and Rest/phaze denial correctly.

Verdict: failed focused repair check. The post-`927928` patch was directionally
useful but incomplete. The missing structure is not "always cash out before
handoff." It is a staged comparison: support job, reset denial, active package,
then handoff.

## Turn 1

Public state: Cloyster mirror.

My answers: Spikes for both sides. Toxic was the main alternative to punish the
opposing Cloyster before it can settle into a support loop.

Actual choices: p1 Toxic miss, p2 Spikes.

Grade: p1 top miss but acceptable; p2 top. Positive-selection both yes.

Lesson: in Cloyster mirror, Spikes and Toxic are both live converters; exact
top is player-side and set-context sensitive.

## Turn 2

Public state: p1 Cloyster with Toxic revealed, p1 side has Spikes; p2 Cloyster
with Spikes revealed.

My answers: p1 Spikes to equalize; p2 Toxic to punish Cloyster or an incoming
receiver.

Actual choices: both switched to Raikou.

Grade: both top miss, both acceptable. Route-conversion partial, branch-punish
miss.

Lesson: this was an owner-pair miss, not a hidden-info miss. Both players
left the support mirror for Electric ownership rather than continuing the
visible support script.

## Turn 3

Public state: Raikou mirror, p1 side Spikes, p1 Raikou 94, p2 Raikou 100.

My p1 answer: switch Ground/Snorlax owner; Thunder was an alternative for
active pressure and paralysis.

My p2 answer: switch Snorlax/Ground owner.

Actual choices: p2 Snorlax, p1 Thunder, which paralyzed Snorlax.

Grade: p1 top miss but acceptable; p2 top.

Lesson: active pressure can beat the handoff when it hits the next owner hard
enough. This is the opposite boundary of owner autopilot.

## Turn 4

Public state: p1 Raikou 99 vs p2 paralyzed Snorlax 77.

My p1 answer: Thunder again to convert paralysis and damage.

My p2 answer: physical attack into Raikou or its Normal-resist branch; I
overranked immediate damage over setup.

Actual choices: p1 Thunder miss, p2 Curse.

Grade: p1 top; p2 top miss but acceptable. Role-package update begins: Snorlax
is now a Curse package, not only a special sponge.

Lesson: Curse is a converter when the extra boost changes the owner board.

## Turn 5

Public state: p1 Raikou vs +1 paralyzed Snorlax 83.

My p1 answer: switch to a physical owner/phazer; p2 should attack if not fully
paralyzed.

Actual choices: p1 Cloyster, p2 fully paralyzed.

Grade: p1 acceptable by physical-wall/support owner class; p2 unscored.

Lesson: spectator-public exact owner can be unknowable, but the class matters.
Cloyster was the support route, not a random sack.

## Turn 6

Public state: p1 Cloyster 94, p1 side Spikes, vs +1 paralyzed Snorlax 89.

My p1 answer: Explosion if owned, with Surf/Spin fallback. This overcorrected
from the prior Steelix cash-out miss.

My p2 answer: attack before more setup.

Actual choices: p1 Spikes, p2 Double-Edge.

Grade: p1 top miss and not acceptable; p2 top. Positive-selection p1 no.

Lesson: cash-out does not lead while the support job is still undelivered and
the target is not exact. Spikes changed the route immediately; Explosion was a
premature spend.

## Turn 7

Public state: both sides now have Spikes; p1 Cloyster 47 vs +1 Snorlax 88.

My p1 answer: now Explosion, because the support job was delivered; handoff was
an alternative if a Normal resist existed.

My p2 answer: switch a revealed absorber if available, otherwise attack.

Actual choices: p1 Steelix, p2 Double-Edge.

Grade: p1 top miss but acceptable as side-known owner gap; p2 top miss but
acceptable. No hidden-info error because the exact Steelix slot was not public.

Lesson: after support is delivered, the spend/save gate must still compare a
known owner handoff. In player-side mode, hidden own team slots would make this
top; in spectator-public mode score it by class.

## Turn 8

Public state: p1 Steelix 76 vs +1 paralyzed Snorlax 91, both sides Spikes.

My p1 answer: Roar to deny the boosted Snorlax and convert Spikes.

My p2 answer: switch/coverage into Steelix, with Rest underpriced.

Actual choices: p1 Curse, p2 Rest.

Grade: both top miss but acceptable. Role-package obeyed only partially.

Lesson: Steelix can boost with Curse into CurseLax, while Snorlax's Rest
resets paralysis and HP. The next turn must ask how to deny that reset.

## Turn 9

Public state: p1 +1 Steelix 82 vs sleeping +1 Snorlax 100, both sides Spikes.

My p1 answer: Curse again; Roar was underpromoted.

My p2 answer: Sleep Talk if owned or passive sleep turn; I missed the switch.

Actual choices: p2 switched Cloyster, p1 Roar dragged Skarmory.

Grade: both top miss; p1 not acceptable because Roar was the reset-denial
converter after Rest. p2 acceptable as a side-known switch route.

Lesson: after the Rest reset, Steelix's Roar is the one-cycle converter with
Spikes. More Curse repeats unstable progress unless the next boosted hit or
Explosion is named.

## Post-Score Study

The focused check shows a retrieval/staging failure. The tiny cards were small
enough, but I loaded owner/package/branch and failed to include the two cards
that govern this exact position: `spend_or_save_piece.md` and
`reset_loop_denial.md`.

Current Smogon sources back the staged interpretation. Steelix's GSC package is
Earthquake, Curse, Roar, and Explosion; Roar phazes threats and forces Spikes
damage, while Explosion is a later conversion when a foe is chipped or cannot
be phazed safely. GSC threat material also says Steelix's Curse + Roar line
boosts alongside physical threats and then phazes to penetrate with Spikes and
boosted Earthquakes. That means the live order must be:

1. Has the support job been delivered or become irrelevant?
2. Has the opponent just reset with Rest, Recover, Spin, or phaze?
3. Does Roar/Whirlwind, pressure, or handoff deny the reset now?
4. Only after those gates, compare Explosion, coverage, setup, and owner
   handoff.

## Structure Patch

Updated the live structure so "one-cycle converter" does not become "cash-out
bias":
- `live_core.md`: role-package selector now points cash-out/rest positions to
  spend/save and reset-loop cards.
- `role_package_ledger.md`: one-cycle pricing is staged through support and
  reset gates, not automatic promotion.
- `spend_or_save_piece.md`: cash-out requires job delivery or irrelevance.
- `reset_loop_denial.md`: after Rest on a boosted target, phaze or force-out is
  often the immediate converter with Spikes.

## Next Rep

Next fresh packet must load the one-cycle packet when cash-out, support job, or
Rest/phaze appears: `role_package_ledger.md`,
`name_next_board_owner.md`, `branch_punish_ranking.md`,
`spend_or_save_piece.md`, and `reset_loop_denial.md`. This is not a fixed card
limit; it is the currently relevant set.
