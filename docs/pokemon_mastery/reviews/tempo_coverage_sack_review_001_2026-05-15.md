# Tempo Coverage/Sack Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/tempo_coverage_sack_transfer_001_gen2ou-2605134773_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. It missed Cloyster's Icy Wind before Spikes
as tempo coverage, Zapdos Rest as a reset branch, and a low Tyranitar defensive
sack that preserved Gengar against boosted Snorlax.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/low_cloyster_cashout_review_001_2026-05-15.md`

Current web sources:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Cloyster OU Revamp:
  `https://www.smogon.com/forums/threads/cloyster-ou-revamp-qc-2-2-gp-2-2.3652352/`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Gengar WIP:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Introduction to Status Moves in GSC:
  `https://www.smogon.com/forums/threads/introduction-to-status-moves-in-gsc.3448819/`

## Confirmed Source Lessons

Cloyster tempo coverage:
Smogon Spikes material treats Cloyster as the most splashable Spiker, but also
as a wallbreaking and tempo piece. The Spikes article specifically notes Icy
Wind as a way to gain speed advantage against Starmie while keeping Spikes
pressure. Cloyster analyses also describe Surf and Explosion as part of why
Normal resists, Ground-types, and spinners cannot enter for free. The replay's
Icy Wind into Surf sequence fits this: tempo coverage removed Nidoking before
the first layer.

Gengar:
Smogon Gengar material describes Dynamic Punch as useful for Snorlax,
Tyranitar, and Umbreon and as a way to put targets into Explosion range. The
transfer hit the Dynamic Punch selection but then allowed Tyranitar to remove
Gengar with Earthquake. The route lesson is to ask whether the confused target
can still KO the route piece before repeating coverage.

Electric Rest reset:
Zapdos and Raikou commonly use RestTalk structures in GSC. Rest is not a public
fact until revealed, but when a damaged Electric survives the current coverage,
Rest must be priced as the reset branch before treating another hit as clean
conversion.

Defensive sack owner:
The cash-out card already contains the answer: a low or doomed support piece
can be spent as a sack to preserve a higher-value owner. The fresh miss was
not missing the concept; it was failing to apply it when Gengar was the active
boosted-Snorlax owner and low Tyranitar could absorb Earthquake.

## Policy Correction

The existing cards are sufficient, but `hazard_loop_spin_window.md` should add
one explicit tempo-coverage reminder:

1. If the support piece can immediately remove, slow, or force out the active
   threat while surviving, coverage can beat the first layer.
2. The first layer is top when it will convert before the support piece is
   forced out or killed.
3. After a support or coverage success, name the opponent's reset branch:
   Rest, phaze, Spin, Explosion, or defensive sack.

## Measurement Note

Not progress. This run kept severe, hidden-info, state, and mechanics errors at
zero, but top-match fell below the previous limited-positive transfer. Do not
claim a trend.
