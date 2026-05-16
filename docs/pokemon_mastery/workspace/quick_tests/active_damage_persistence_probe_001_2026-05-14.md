# Active Damage Persistence Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_061_active_pressure_transfer_smogtours-gen2ou-911263_2026-05-14.md`.

Mode: constructed nonblind policy regression. This tests the repeated active
damage underpricing from replay 061. It is not fresh replay-transfer evidence.

## Score Summary

Scenarios: 4.

Action policy hits: 4 / 4.

Classification hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Continue Into Cloyster Before Pivoting

Prompt:

Vanilla GSC spectator-public state. Your Snorlax is active at full HP against
an opposing Cloyster at 72%. Cloyster has not yet used Spikes. Last turn,
Snorlax's Double-Edge did meaningful damage as Cloyster entered. You have a
possible Electric pivot, but it is not publicly revealed. Cloyster may set
Spikes, Toxic, switch, or later threaten Explosion.

Question: should Snorlax pivot immediately, or keep attacking?

Frozen answer:

Keep attacking by default. Double-Edge is already turning Cloyster from a full
support piece into a low, timing-sensitive piece. Pivot only if the pivot
prevents a concrete branch that Double-Edge cannot, such as a known Explosion
trap, a protected spinner route, or a teammate that enters without giving up
the damage clock.

Answer key:

Hit. Replay 061 showed the second Double-Edge was still the route before
pivoting. The damage changed Cloyster's future Spikes, Spin, and Explosion
map.

## Scenario 2 - Continue Into Forretress Through Reflect

Prompt:

Vanilla GSC spectator-public state. Your Snorlax is active at full HP. The
opponent has Zapdos at 81% behind Reflect and Forretress at 77%. Spikes are on
the opponent's side. The opponent may switch Forretress into Double-Edge again.
You can pivot to Golem to block Thunder, but Golem gives Forretress a freer
support turn if Zapdos leaves.

Question: should Snorlax switch because Reflect is up?

Frozen answer:

Not automatically. If Snorlax's next Double-Edge plus Spikes puts Forretress
into a range where its future support job is worse, keep attacking. Reflect
reduces damage, but it does not erase the route if the opponent is still being
forced through losing support entries. Switch only if Thunder or a setup branch
is more important than continuing the support-piece damage clock.

Answer key:

Hit. Replay 061 showed Double-Edge into Forretress through Reflect still made
progress. The mistake was treating Reflect as a stop sign instead of pricing
the next support-map damage.

## Scenario 3 - Preserve Low Cloyster When Explosion Is Covered

Prompt:

Vanilla GSC spectator-public state. Your Cloyster is at 44% after setting
Spikes. It faces a full HP Snorlax. The opponent has a revealed Gengar at high
HP and Spikes are on the opponent's side. Cloyster has not revealed Explosion.

Question: is Explosion into Snorlax the default?

Frozen answer:

No. Explosion is tempting, but the revealed Ghost makes the obvious cash-out
branch easy to cover. Preserve or pivot Cloyster unless the trade removes a
named blocker and the Ghost switch is either impossible, punished, or not
route-relevant. Low Cloyster still has threat value after setting Spikes.

Answer key:

Hit. Replay 061 punished the auto-boom line: p1 preserved Cloyster and p2
switched Gengar to cover the obvious Explosion/Normal branch.

## Scenario 4 - Counter-Switch After Reading Their Switch

Prompt:

Vanilla GSC spectator-public state. Your Golem is active against opposing
Gengar at 94%. Spikes are on the opponent's side. You believe Gengar is likely
to switch to Zapdos to dodge Earthquake. You have Snorlax available and healthy
enough to meet Zapdos.

Question: should Golem Earthquake anyway?

Frozen answer:

No by default if the Zapdos switch is the named best branch. Counter-switch to
Snorlax or the appropriate Zapdos answer instead of taking the obvious active
move into the absorber. Earthquake is correct only if staying Gengar is likely
enough or if the switch punish is not worth giving up Golem's position.

Answer key:

Hit. Replay 061 showed p1 switching Snorlax as p2 switched Zapdos. Naming the
opponent's switch is not enough; the move must act on that branch.

## Reusable Boundary

Active pressure is persistent when the next hit changes the opponent's support
map, not only when it scores a KO. Stay with it through resist entries,
Reflect, or support threats until a concrete branch flips the exchange.

## Next Transfer Check

Run a fresh no-keyword-screen replay packet on active-damage persistence. The
target question is: does the next hit change the opposing support piece's job,
or is this the turn to pivot, status, phaze, or cash out?
