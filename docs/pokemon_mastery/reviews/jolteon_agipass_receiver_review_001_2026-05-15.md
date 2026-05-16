# Jolteon AgiPass Receiver Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/jolteon_agipass_receiver_transfer_001_smogtours-gen2ou-935550_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect and stopped early. Severe-blunder avoidance
passed, but the actual weakness was positive selection: I saw Baton Pass once,
then failed to treat the next Jolteon turn as a boost-plus-receiver route. The
same packet also missed a named Zapdos receiver and a Snorlax route owner into
Jolteon's public package.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/bp_chain_revealed_coverage_review_001_2026-05-15.md`
- `workspace/quick_tests/bp_chain_revealed_coverage_transfer_001_smogtours-gen2ou-933681_2026-05-15.md`
- `reviews/pass_package_sleeper_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/pass_package_sleeper_handoff_transfer_001_gen2ou-2608087104_2026-05-15.md`
- `workspace/quick_tests/agipass_machamp_explosion_guard_transfer_001_smogtours-gen2ou-933493_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist, Jolteon section:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC OU Speed Tiers:
  `https://www.smogon.com/resources/competitive/gs/gsc_speedtiers`
- Smogon Forums GSC OU Speed Tiers:
  `https://www.smogon.com/forums/threads/gsc-ou-speed-tiers.3687306/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums GSC BP:
  `https://www.smogon.com/forums/threads/gsc-bp.3541165/`

## Source-To-Policy Extraction

Jolteon is a package tell once Baton Pass is public:
Smogon GSC material describes Jolteon as a preferred Baton Pass user that can
pass Agility, Growth, and Substitute. The GSC BP source uses the explicit
Thunderbolt / Hidden Power Water / Agility / Baton Pass Jolteon structure.
Therefore a dry Baton Pass from Jolteon is not neutral switch information; it
is public evidence that later boost turns and receivers must be ranked.

Agility changes receiver boards, not just speed:
The speed-tier sources frame Agility pass by asking which receiver outspeeds
which answers after the boost. They list Agility recipients such as Machamp,
Marowak, Snorlax, and others. The decision rule is to name the receiver and
the defender's answer before clicking direct damage or a plain pass.

Full-pass structures make one missed turn decisive:
The sample-team source identifies a standard Agility Baton Pass structure with
Smeargle, Scizor, Snorlax, Marowak, Jolteon, and Machamp, and emphasizes that
a single misplay can let the pass route snowball. The training lesson is not
to fear every possible chain; it is to reclassify once public moves make the
package coherent.

Receiver discipline remains no-Team-Preview:
Before Machamp, Marowak, or Snorlax is revealed, exact receiver names are
possible-only unless public material shows them. The correct recommendation can
say "Agility/pass to the physical breaker class with attack fallback" without
anchoring on a hidden exact teammate. Once Machamp appears, later Jolteon
boost/pass lines can name it.

Defensive response must name the package answer:
Against public Jolteon Baton Pass, the defender should rank attack, phaze if
revealed or strongly supported, special/normal owner such as Snorlax, Ground
or Rock counter-pivot, and pressure on the actual receiver. In this transfer,
my defender answer stayed generic Zapdos pressure and missed Snorlax entering
to meet the package.

## Policy Updates Made

- `branch_action_after_naming.md`: added a dry-pass reveal extension so a
  fast Electric or support piece that has shown Baton Pass reopens
  Agility/Growth/Substitute and receiver-denial lines on the next sighting.
- `active_context.md`: moved the latest fresh-transfer pointer from lead sleep
  to `jolteon_agipass_receiver_transfer_001` and made the next rep focus on
  public Baton Pass package re-solving.
- `measurement_progress_ledger.csv`: recorded the early-stop transfer and the
  constructed regression probe separately.

## Measurement Note

Not progress. The packet went 2/10 top and 5/10 acceptable with 0 severe,
hidden-info, state, and mechanics errors. Positive-selection was 7/10, but
route conversion was only 5/10 and branch-punish obedience was 4/8. The clean
severe gate means only that catastrophic errors stayed low; it does not show
better move choice because the route-improving decisions were still missed.

The regression probe below is allowed as a local repair check only. It is not
fresh unseen evidence and cannot be used to claim mastery or boss-sim
validation.
