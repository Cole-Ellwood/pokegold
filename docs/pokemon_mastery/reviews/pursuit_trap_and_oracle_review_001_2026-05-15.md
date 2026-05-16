# Pursuit Trap And Oracle Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_034_gen2ou-2585322715_p1_2026-05-15.md`

## Diagnosis

The packet exposed two separate issues:

1. A real live-play miss: I treated Gengar versus Umbreon as a normal
   preserve-or-switch decision after Pursuit was revealed. It was not. Pursuit
   made switching the punished branch, so the trapped Gengar needed to spend
   with Thunder, DynamicPunch, Destiny Bond/Explosion if available, or another
   named converter before preservation could be top.
2. A method/scoring issue: exact replay top-match was noisy. The actual player
   repeatedly clicked Thunder into Umbreon, which is high-variance but worked
   after paralysis/confusion. That exact line should affect top-match, but it
   should not be the only signal used to decide whether the compact docs are
   improving route advice.

The severe gate stayed repaired, but this is still not progress because the
three-packet post-repair sample missed the exact-top target.

## Source Check

Current GSC sources support the correction:

- Smogon's Umbreon analysis describes Pursuit as a way to wear down Gengar,
  Exeggutor, and Misdreavus, with extra punishment if they switch.
- Smogon's Gengar analysis says Gengar is highly vulnerable to Umbreon and
  Tyranitar Pursuit, while DynamicPunch is a coverage option that helps damage
  Pursuit users.
- Smogon's sample-team breakdown notes that Gengar and Exeggutor may need to
  use Explosion or other immediate pressure against Umbreon when it enters to
  trap them.
- Smogon's GSC Spikes article supports the late-packet hazard lesson:
  Tentacruel is a real spinner, while Cloyster is central to re-establishing
  Spikes when passive turns appear.

Sources:

- https://www.smogon.com/forums/threads/umbreon-ou-revamp-qc-2-2-gp-2-2.3624491/
- https://www.smogon.com/forums/threads/gengar-update-qc-2-2-gp-2-2-done.3472865/
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- https://www.smogon.com/gs/articles/gsc_spikes

## Policy Compression

Patch one live rule into `spend_or_save_piece.md`:

> If preservation requires switching through revealed Pursuit/trap damage,
> compare spend-now against the HP/job left after the escape. Do not call the
> switch preservation unless the future job survives and is named.

No new species card is needed. Umbreon/Gengar is just the trap version of the
spend-or-save piece rule.

## Method Change

Patch `replay_turn_pause_protocol.md` so each post-score review can label
actual-move oracle quality:

- `clean`: actual move is a strong pro-comparison top.
- `route_equivalent`: actual differs but follows the same route.
- `style_or_variance`: actual is plausible but high-variance or stylistic.
- `own_move_gap`: helper lacks the advised side's full legal move list.
- `unscored`: log cannot recover the intended move or the turn is forced.

Exact `top_match` remains mandatory; this label does not erase misses. It
prevents overfitting compact docs to one player's high-variance exact move when
route-quality, positive-selection, and acceptable-match tell a different story.

## Drill Target

Create one four-case nonblind drill:

- Gengar before Pursuit is revealed can use pressure or leave with a fallback.
- Gengar after Pursuit is revealed should not switch unless survival plus
  future job is named.
- A low trapped Gengar should spend with its best pressure when switching is
  likely to lose the same piece anyway.
- Cloyster should re-enter on a passive Skarmory turn to reset Spikes when the
  spinner branch is still alive.
