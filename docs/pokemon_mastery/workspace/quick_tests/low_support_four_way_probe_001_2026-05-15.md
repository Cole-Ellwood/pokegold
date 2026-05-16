# Low-Support Four-Way Probe 001 - 2026-05-15

Type: focused regression probe after `low_cloyster_ghost_guard_transfer_001`.

Status: nonblind constructed drill. This checks whether the low-support
boundary can be executed as concrete move choices. It is not fresh replay proof
and must not count as mastery progress.

Source basis:

- `policy_cards/cashout_boundary.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/low_cloyster_ghost_guard_review_001_2026-05-15.md`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

## Score Summary

Scenarios: 6.
Top-match: 6 / 6.
Acceptable-match: 6 / 6.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 6 / 6.
Route-converting move chosen: 6 / 6.
Branch-punish chosen: 6 / 6.

Result: pass as regression only. The answers separate preservation, coverage
or status, Explosion, defensive sack, and Ghost guard without turning any one
branch into a script.

## Scenario 1 - Status Before Leaving

Public state:
p1 Cloyster is active at 34% against p2 Snorlax at 87%. p1 has already set
Spikes on p2's side. Cloyster has revealed Spikes and Toxic. p2 Snorlax has
revealed Double-Edge and Earthquake and is not statused. p1 has Zapdos and
Jynx revealed in back. No Ghost is revealed for p2.

Frozen answer:
Top action: Toxic. Confidence: medium-high.

Ranked candidates:

1. Toxic.
2. Switch Zapdos if Snorlax is likely to attack and Cloyster's later job is
   more valuable.
3. Explosion only as a high-risk read if slow play loses and no guard enters.

Reason:
Cloyster's Spikes job is done, but Snorlax is still the active route piece.
Toxic changes the timer before Cloyster leaves. Explosion is live, but it
spends Cloyster before using the revealed status that improves the next board.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Preserve The Low Support Piece

Public state:
p1 Cloyster is active at 34% against p2 Snorlax at 87% toxic-poisoned. Spikes
are on p2's side. p1 Zapdos is healthy and pressures Snorlax. p2 has no
revealed Ghost, but Gengar is a legal hidden class. Cloyster still threatens
Explosion later and can be a defensive sack if preserved.

Frozen answer:
Top action: switch Zapdos. Confidence: medium.

Ranked candidates:

1. Zapdos handoff.
2. Explosion only if Snorlax staying is required and the Ghost branch is
   explicitly accepted as a read.
3. Surf/Ice Beam chip if Zapdos cannot afford the next board.

Reason:
The timer is already on Snorlax, so preserving Cloyster keeps boom pressure or
a later sack while Zapdos takes over the pressure route. This avoids spending
Cloyster into a plausible Ghost guard when slow play is already improving.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Explosion Converts

Public state:
p1 Cloyster is active at 28% against p2 Snorlax at 62% toxic-poisoned. p1 has
Spikes up on p2's side. p2's Gengar has already fainted, and no Protect or
Substitute user is revealed. If Snorlax Rests, p1 loses the immediate Zapdos
cleaning route. Cloyster has no realistic later entry through Spikes and chip.

Frozen answer:
Top action: Explosion. Confidence: high.

Ranked candidates:

1. Explosion.
2. Surf/Ice Beam chip only if Explosion is unavailable.
3. Switch Zapdos only if Snorlax cannot Rest or escape.

Reason:
The prior support job is delivered, the target is exact, the Ghost guard is
removed, and delay lets Snorlax reset. Explosion removes the blocker and opens
the named Zapdos route.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Defensive Sack Owner

Public state:
p1 Cloyster is active at 18% against p2 Zapdos at 71%. p1 Snorlax is healthy
and needed for the endgame; p1 Raikou is at 43% and cannot take two Thunders.
Cloyster has already set Spikes and poisoned p2 Snorlax. Explosion does not
remove Zapdos from this HP range, and Zapdos is expected to Thunder.

Frozen answer:
Top action: leave Cloyster in as the sack or switch it into the expected hit
if another piece is active. Confidence: medium.

Ranked candidates:

1. Cloyster defensive sack.
2. Switch Raikou only if it must contest Zapdos immediately.
3. Explosion only if the damage creates a named revenge route.

Reason:
The support piece's final job is to absorb the hit and preserve Snorlax/Raikou
for the real route. Spending it this way is positive because the preserved
owner and next board are explicit.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Guard Against Explosion

Public state:
p2 Cloyster is active at 31% against p1 Snorlax at 80%. p2 has set Spikes and
revealed Toxic. p1 Gengar is revealed healthy. p2 Cloyster may explode, Surf,
Toxic, or switch. p1 Snorlax is valuable and does not need to stay to convert
this turn.

Frozen answer:
Top action: switch Gengar. Confidence: medium-high.

Ranked candidates:

1. Gengar guard.
2. Switch low-value Rock/Steel resist if Gengar would lose the next route.
3. Attack only if Cloyster cannot explode or active damage wins immediately.

Reason:
The opposing low support piece has delivered its job and can cash out into
Snorlax. A revealed Ghost guard enters without relying on hidden information
and preserves the central route.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Do Not Treat Possible Ghost As Fact

Public state:
p1 Cloyster is active at 28% against p2 Snorlax at 62% toxic-poisoned. Spikes
are on p2's side. No Ghost, Protect, Substitute, or low-value sack has been
revealed. Gengar is legal but only possible. If Snorlax Rests, the current
route collapses.

Frozen answer:
Top action: Explosion, with possible Ghost named as the losing branch.
Confidence: medium.

Ranked candidates:

1. Explosion.
2. Surf/Ice Beam chip if preserving Cloyster still keeps the route.
3. Switch Zapdos only if Snorlax cannot reset.

Reason:
Possible-only Ghost cannot be treated as fact when delay loses. The answer
names the risk and fallback, but still chooses the route-converting move.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. On every low
support turn, freeze the four-way checklist:

1. Does status or coverage still change the active target?
2. Does preserving the support piece keep a real later job?
3. Does Explosion remove an exact blocker before it can reset?
4. Can the opponent guard with a revealed or plausible Ghost, resist, or
   low-value sack?
