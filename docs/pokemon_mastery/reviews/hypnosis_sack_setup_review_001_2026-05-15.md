# Hypnosis, Defensive Sack, And Setup Review 001 - 2026-05-15

Study status: post-miss web/local review and policy update source. This is not
fresh replay-transfer proof and does not count as progress by itself.

Parent transfer:
`workspace/quick_tests/subspin_named_absorber_transfer_001_smogtours-gen2ou-935833_2026-05-15.md`

Current replay source:

- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935833`
- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935833.log`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Gengar Through the Ages:
  `https://www.smogon.com/articles/gengar-through-ages`
- Smogon, GSC OU Cloyster spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Gengar forum analysis draft:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`

Local docs checked:

- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `workspace/quick_tests/support_entry_explosion_absorber_probe_001_2026-05-14.md`
- `reviews/2026-05-13_smogtours-gen2ou-804450.md`
- `reviews/2026-05-13_smogtours-gen2ou-902727.md`
- `reviews/2026-05-13_smogtours-gen2ou-861526.md`
- `reviews/2026-05-13_smogtours-gen2ou-902742.md`

## Review Question

The fresh transfer improved the tracked metrics, but three misses remained:

- Turn 8: Gengar used `Hypnosis` into the switch while I ranked coverage into
  poisoned Cloyster first.
- Turn 13: the player spent a nearly dead poisoned Cloyster as the defensive
  owner into Surf while I tried to preserve Steelix with Gengar.
- Turn 16: Steelix used `Curse` on the forced Vaporeon switch while I defaulted
  to phazing.

The question is whether these are new rules or existing rules I failed to
apply.

## Evidence

Gengar:

Smogon sources and local reviews agree that Gengar's value is not only raw
coverage. It threatens sleep, broad special coverage, spinblocking, and
Explosion. In the parent replay, Cloyster was already poisoned and likely to
leave; Thunderbolt was good if Cloyster stayed, but Hypnosis was the branch
punish because the switch target could still be slept.

This is an existing branch-action miss. The active target being poisoned does
not make status bad if the intended target is the incoming Pokemon.

Cloyster:

Smogon's Spikes material and Cloyster spotlight frame Cloyster as a support
piece that often trades durability for Spikes, Toxic, Surf pressure, or
Explosion. Local reviews show the same pattern: once a degraded support piece
has delivered its field job, it may be spent as a sack, Explosion user, or
defensive owner to preserve a higher-value route piece.

Turn 13 was not "save Cloyster." Cloyster was already doomed by Spikes plus
poison. The better question was which remaining piece should take Surf. The
actual answer spent the low Cloyster and kept Gengar and Steelix cleaner.

Steelix:

The GSC Threatlist and local reviews describe Steelix as a phazer, Electric
check, Snorlax answer, setup piece, and Explosion threat. Phazing is valuable
with Spikes, but it is not always the best branch action. If Steelix has forced
Snorlax out and the incoming Water is predictable, `Curse` can make the switch
turn a setup turn. The follow-up still needs a Water owner, but the first
positive move is not automatically Roar.

## Policy Updates

Status into switch:

If the visible active is already poisoned, immune, or likely to leave, do not
discard sleep/status automatically. First ask whether the named switch target
can still be statused and whether that status changes the route more than
coverage into the current active. This is especially live for fast Gengar and
Exeggutor-style positions where the current target invites a hard answer.

Defensive sack owner:

A low support piece can be spent without using Explosion. If it is already
doomed by Spikes, poison, or matchup and can absorb the expected attack while
preserving a higher-value route owner, the switch-sack can be the positive
selection. Name the preserved piece and the next board; otherwise it is just a
sentimental sack.

Setup versus phaze:

When a phazer or normal resist has forced the current threat out, rank setup
beside phaze and direct pressure. Phaze is top when repeated entries are the
route or the current threat cannot be allowed to stay. Setup is top when the
switch is forced, the boost improves the next board, and the incoming answer
does not immediately erase the route.

## Not A Progress Claim

The parent transfer is a limited positive transfer, not mastery:

- The replay is unseen by ID, but it has a same-pair caveat.
- The score improved across the tracked metrics, but one run is not a trend.
- No boss-sim, romhack mechanics, or final-exam validation follows from it.

Next proof should use a different player pool if the current replay search
allows it, with status-into-switch and low defensive-sack owner checks active.
