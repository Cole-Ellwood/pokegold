# Support Spend / Perish Receiver Review 001 - 2026-05-15

Parent packet:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_027_gen2ou-2588552337_p1_2026-05-15.md`

Trigger: packet 027 had no severe or hidden errors, but top-match stayed low.
The main misses were not missing raw mechanics; they were timing errors around
when to spend a support piece and how Perish Song can force a receiver.

## Sources Checked

- Pokemon Showdown replay and raw log:
  `https://replay.pokemonshowdown.com/gen2ou-2588552337`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Gengar through the ages:
  `https://www.smogon.com/articles/gengar-through-ages`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Lesson

Smogon Spikes material frames Cloyster as a support piece that still creates
offensive pressure with Spikes and Explosion. The packet showed the live
boundary: after Cloyster is already the selected support sack into a boosted
physical threat, setting Spikes before dying can be the route-converting spend.
Guarding an unconfirmed Explosion or chasing an unshown self-KO can be an
overcorrection if the support job is unfinished.

Smogon Gengar material reinforces that Perish Song and Destiny Bond are part
of Gengar's disruptive package, not just emergency buttons. In packet 027,
Perish Song into Umbreon forced the opponent to leave; Mean Look then trapped
the receiver. I treated "trap before perish" as too strict. The correct live
rule is conditional: Perish before trap is allowed when the receiver and exit
plan are named immediately.

The Machamp source reminder matters for the Cloyster turn: +1 critical Cross
Chop is a real OHKO threat into non-resists. That does not mean panic-switch
every time; it means the support piece must either complete a job before the
hit, use an exact removal if legal, or hand off to a named absorber.

## Repair Rule

Before guarding a support piece, ask whether its job can complete before it
dies. If yes, spending it for Spikes/status/boom can be the positive move.

For Perish routes, solve hold -> count -> exit, but allow count -> forced
receiver -> hold when the first Perish Song is used specifically to create a
trap target. Do not call that progress unless the receiver and exit are named.
