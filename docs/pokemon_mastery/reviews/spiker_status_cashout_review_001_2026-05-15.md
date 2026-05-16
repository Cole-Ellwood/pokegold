# Spiker Status / Cash-Out Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_032_gen2ou-2585447000_p2_2026-05-15.md`

## Miss Pattern

Packet 032 rebounded on top-match and kept severe errors clean, but T15 was a
real miss. I switched Raikou into an unrevealed opposing Cloyster because the
active Water target looked easy to pressure. That skipped the package ledger:
Cloyster's live job was not only "Water weak to Electric." It was Spikes,
Toxic, and possible Explosion after or during support delivery.

The actual player used Umbreon, a lower-value status/cash-out absorber. Toxic
missed, but the route idea was correct: keep Raikou clean for Zapdos and later
special-wall jobs unless Electric pressure converts before Toxic or Explosion
can damage that route piece.

## Source Check

Current GSC sources support the correction:

- Smogon's GSC Spikes article describes Cloyster as the most splashable Spiker
  because it combines Spikes with offensive pressure from Surf and Explosion.
- Smogon's Cloyster analysis thread lists Surf, Spikes, Toxic, and Explosion
  as the core package and explains that Toxic pressures opposing Cloyster,
  Starmie, and Curse Snorlax while Explosion lets Cloyster trade after Spikes.
- Smogon's GSC sample-team breakdown repeatedly frames Cloyster's job as
  keeping Spikes up, spreading Toxic, and using Surf plus Explosion to threaten
  broad trades.

Sources:

- https://www.smogon.com/gs/articles/gsc_spikes
- https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/
- https://www.smogon.com/forums/threads/cloyster-ou-revamp-qc.3622706/
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/

## Local Doc Check

The lesson already exists in compressed form:

- `role_package_ledger.md` asks whether a typed/status absorber preserves the
  generic wall and whether the revealed package enables or denies an owner.
- `public_info_tiers.md` says strong-prior status can promote a typed or
  status-tolerant absorber over generic bulk.
- `spend_or_save_piece.md` already handles low support and cash-out branches
  after support jobs are delivered.

The missing live wording was that a spiker entering into its job should be
priced as a support package before a valuable route piece attacks it. This is
one compact rule, not a new long policy card.

## Policy Compression

Patch `role_package_ledger.md` with one general spiker-package question:

> If a spiker enters into its support job, price Spikes/Toxic plus cash-out or
> Spin before routing a valuable route piece through it.

## Drill Target

Create a four-case nonblind regression drill:

- do not route Raikou into unrevealed Cloyster when Umbreon can absorb
  Toxic/Explosion;
- Toxic Zapdos before switching Raikou when active status converts;
- Pursuit Cloyster when it is likely leaving after support delivery;
- Rapid Spin with Golem when dragged in and the active threat cannot remove it
  before the spin.
