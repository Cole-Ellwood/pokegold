# AgilityPass Reflect / Spin Review 001 - 2026-05-15

Parent packet:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_028_gen2ou-2586070153_p1_2026-05-15.md`

Trigger: packet 028 was positive but not perfect. The misses were narrow enough
to patch compactly: Reflect as a pass-receiver answer, Starmie Rapid Spin over
exact damage, and residual-faint action order.

## Sources Checked

- Pokemon Showdown replay and raw log:
  `https://replay.pokemonshowdown.com/gen2ou-2586070153`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon GSC OU Speed Tiers:
  `https://www.smogon.com/resources/competitive/gs/gsc_speedtiers`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Lesson

The sample-team and speed-tier sources reinforce that Jolteon AgilityPass is a
receiver-map problem. The important question is not "can I hit Jolteon?" but
"which receiver acts before my answer, and can Reflect/phaze/status make that
receiver fail?" In packet 028, Reflect was repeatedly the actual converter
because it let Snorlax, Tyranitar, and Raikou survive the pass route.

The Spikes sources reinforce Starmie's support identity: Rapid Spin is its job,
and Starmie often has to spin on the switch rather than wait for a perfect
active-target attack. In packet 028, Psychic into low Cloyster was tempting,
but Rapid Spin covered the Jolteon switch and removed the reset loop.

The raw replay supplied the mechanics note: after Marowak attacked, poison
damage KOed it before slower Forretress could move. That means slow support
spend cannot be counted when the active target will faint to residual before
the slower move executes.

## Repair Rule

For AgilityPass, rank answers in this order:

1. receiver survives? If not, Reflect or status may be the converter;
2. phazer can enter and survive? If yes, Roar/Whirlwind;
3. Encore only if the passer stays or the receiver can be punished;
4. active damage only if it beats both passer and receiver branch.

For Starmie, Rapid Spin beats exact damage when hazards are already up, the
spiker can switch, and the spin will complete before the punishment.

For residual KO, if the faster target will faint to poison after its action,
do not rely on the slower selected move happening.
