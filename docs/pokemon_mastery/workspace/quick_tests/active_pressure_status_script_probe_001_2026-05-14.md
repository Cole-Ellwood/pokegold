# Active Pressure Status Script Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_060_fixed_helper_phaze_transfer_smogtours-gen2ou-912658_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 060's
active-pressure lessons are now usable decision boundaries. It is not fresh
replay-transfer evidence.

## Score Summary

Scenarios: 4.

Action policy hits: 4 / 4.

Classification hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Snorlax Damage Before Pivoting

Prompt:

Vanilla GSC spectator-public state. Your Snorlax is active at 100% against an
opposing Cloyster at 77%. Snorlax just used Double-Edge into a Zapdos-to-
Cloyster switch and did about 29% before Leftovers. No hazards are up yet.
Cloyster may set Spikes, Toxic, switch, or threaten Explosion later. Your
Electric pivot exists but is not currently revealed.

Question: should Snorlax pivot immediately to an Electric, or keep pressing?

Frozen answer:

Keep pressing with Double-Edge by default unless a known teammate has a cleaner
entry that changes the hazard or Explosion branch. Snorlax's damage is already
converting: another hit can put Cloyster near the range where it cannot set
hazards, spin, or boom comfortably. Pivoting only because Cloyster is a Spiker
can give up the active pressure that is currently winning the exchange.

Answer key:

Hit. Replay 060 showed Double-Edge was still the route after Cloyster entered.
The mistake was leaving active damage before the opponent showed a branch that
required a handoff.

## Scenario 2 - Poisoned Support Before Explosion

Prompt:

Vanilla GSC spectator-public state. Your Cloyster is poisoned at 94% and has
set Spikes. The opponent's Zapdos is active at 100%, and Spikes are on both
sides. Your Snorlax is healthy enough to absorb one Thunder sequence. Cloyster
has not revealed Explosion or Rapid Spin.

Question: should Cloyster immediately explode into Zapdos?

Frozen answer:

No by default. Preserve or hand off first unless Explosion opens a named
converter that Snorlax cannot cover. Poisoned Cloyster still has route value:
it may reset hazards, threaten Explosion later, absorb a physical hit, or
force the opponent to keep respecting it. Snorlax taking Thunder is a cleaner
short-term answer than spending Cloyster into a full-HP Zapdos without a named
conversion.

Answer key:

Hit. Replay 060 punished the auto-Explosion instinct. The poisoned support
piece still had a job, and Snorlax was the immediate Thunder absorber.

## Scenario 3 - Roar When The Switch Is Likely

Prompt:

Vanilla GSC spectator-public state. Your Steelix is active at 90% against an
opposing Tyranitar at 100%. Spikes are on both sides. Tyranitar has revealed
Rock Slide. Steelix threatens Earthquake, and the opponent has already shown a
Zapdos and Cloyster, with other unrevealed teammates likely to dislike repeated
Spikes entries.

Question: Earthquake or Roar?

Frozen answer:

Roar is the default if the opponent is likely to leave the Earthquake threat.
The route is not just damaging Tyranitar; it is punishing the switch cycle
through Spikes while Steelix stays healthy enough to keep phazing. Earthquake
becomes better if Tyranitar is likely to stay and the damage changes a concrete
range or prevents a stronger punish.

Answer key:

Hit. Replay 060's clean transfer was Steelix using Roar into the expected
switch and then again after the direct hit did not break the route.

## Scenario 4 - Status-Capable Does Not Mean Status-Forced

Prompt:

Vanilla GSC spectator-public state. Your Exeggutor is active at 82% against an
opposing Steelix at 77%. Spikes are on both sides. Exeggutor can plausibly have
Sleep Powder, but Steelix is the active target and takes meaningful damage from
Psychic. The opponent has a sleeping Snorlax available as a possible absorber.

Question: should Exeggutor default to Sleep Powder?

Frozen answer:

No. Price the direct Psychic first. Sleep Powder is strong only if it changes a
route that Psychic or a switch cannot, and the sleeping Snorlax absorber makes
the sleep branch less clean. If Psychic pressures Steelix while preserving
tempo and avoiding the absorber branch, direct damage is the better default.

Answer key:

Hit. Replay 060 repeated the sleep over-script error: Exeggutor used Psychic,
not Sleep Powder, because the active board already offered progress.

## Reusable Boundary

Status, Explosion, and pivots are tools, not scripts. Before choosing them,
ask whether the active move already improves the route through damage, forced
switches, hazard conversion, or role preservation. Use status or cash-out only
when it beats that live pressure line or covers a named worst branch.

## Next Transfer Check

Run a fresh no-keyword-screen replay packet focused on active pressure versus
status script. Stop after the first two repeated misses or after 20-30 side
decisions, then update only the active-pressure policy if the boundary changes.
