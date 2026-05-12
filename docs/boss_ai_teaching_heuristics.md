# Boss AI Teaching Heuristics

Purpose: preserve the user's boss-battle judgment as readable rules before
turning it into synthetic examples, debugger weights, or ROM scoring changes.

This file is the working sheet for the hybrid teaching loop. A rule should not
be promoted into ROM behavior just because it appears here; it needs matching
fixtures, passing audits, and a clear implementation target.

## Workflow

1. Ask the user a concrete public-info boss state from the training lab.
2. Record the answer as a rule, exception, or open question here.
3. Save the matching preference or trajectory row in the lab data.
4. Re-run reports to check for conflicts, stale source rows, and coverage gaps.
5. Generate synthetic examples only from stable, high-confidence rules.
6. Keep user-authored examples weighted above synthetic examples.
7. Promote a rule to ROM scoring only when the behavior is clear and testable.

## Synthetic Data Rules

- Synthetic examples are allowed for obvious cases, not taste calls.
- Synthetic rows must stay marked as synthetic when generated.
- Do not generate synthetic labels from a rule with unresolved exceptions.
- Do not use synthetic data to override a direct user answer.
- Prefer small batches that can be spot-checked before larger batches.

## Current Heuristics

### Immediate KO Beats Slow Play

- Status: stable
- Type: weight hint
- Rule: If a move reliably KOs or nearly KOs the active target now, prefer it
  over slow status, passive recovery, weak chip, or greedy setup.
- Applies when: the boss can take the KO without exposing a more valuable plan.
- Does not apply when: the KO move creates a worse forced lock, misses a better
  safe switch, or the target has a known public countermeasure.
- Example fixtures:
  - `koga_crobat_vs_alakazam_toxic_or_attack`
  - `morty_gengar_vs_kadabra_destiny_bond`
  - `misty_starmie_vs_meganium_recover_or_attack`
- Implementation target: debugger scoring first; ROM move scoring after review.

### Setup Must Change The Damage Race

- Status: stable
- Type: sequence policy
- Rule: Setup is good when it changes the next-turn damage race, creates a KO
  window, or leaves the boss ahead after the expected punish. Do not click setup
  merely because the boss is a setup-style Pokemon.
- Applies when: the boss survives, the setup improves KO math, or the player is
  unlikely to punish immediately.
- Does not apply when: the player has revealed lethal pressure, setup does not
  change the number of turns to win, or the boss loses too much tempo.
- Example fixtures:
  - `bugsy_scyther_vs_quilava_fire_pressure`
  - `clair_kingdra_vs_lapras_dragon_dance_or_attack`
  - `whitney_clefairy_vs_bayleef_encore_window`
  - `erika_victreebel_vs_snorlax_sleep_or_boost`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Implementation target: plan scoring, then ROM setup weights.

### Sleep Is Strong But Must Be Gated

- Status: stable
- Type: hard rule
- Rule: Sleep is legal and strong; do not avoid it just because it feels mean.
  Gate it only on real public fail states such as Sleep Clause, an already
  statused target, Substitute, Safeguard, or repeating sleep after it already
  landed. A landed sleep can justify one setup turn, then the boss should cash
  damage and only reapply sleep after the target wakes and Sleep Clause allows
  it.
- Applies when: target is awake, legal to sleep, and the miss risk is worth the
  control.
- Does not apply when: the boss can simply KO now, Sleep Clause blocks it, or
  missing loses a decisive race.
- Example fixtures:
  - `morty_haunter_vs_noctowl_sleep_line`
  - `erika_victreebel_vs_snorlax_sleep_or_boost`
  - `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Implementation target: sleep fail gates and status scoring.

### One Debuff Can Be Right, Repeating Debuffs Usually Is Not

- Status: stable
- Type: sequence policy
- Rule: One accuracy or control debuff can be good when direct damage is nearly
  worthless. Repeating debuffs is usually bad because the player can switch and
  clear them.
- Applies when: chip damage is negligible and one debuff materially improves
  survival or tempo.
- Does not apply when: useful damage is available, the target can freely switch,
  or the boss is spending multiple turns for no lasting gain.
- Example fixtures:
  - `falkner_pidgeotto_vs_geodude_rock_risk`
- Implementation target: sequence memory and repeat-utility penalties.

### Avoid Bad Lock-In Openers

- Status: stable
- Type: hard rule
- Rule: Do not begin a ramp or lock-in move like Rollout or Outrage when it is
  resisted, does not KO, and gives the player a clear punish or switch.
- Applies when: the lock-in move starts from a weak position.
- Does not apply when: the target is already in KO range, paralyzed, unable to
  punish, or the lock sequence is already safely underway.
- Example fixtures:
  - `whitney_miltank_vs_geodude_rollout_temptation`
- Implementation target: lock-move opener scoring.

### Switch When Preservation Is Worth The Free Hit

- Status: developing
- Type: switch policy
- Rule: Switching is good when preserving the active boss Pokemon is worth more
  than the free turn the player gets, especially if the bench has a clear resist
  or a better threat.
- Applies when: the current active is likely to lose or has high later value.
- Does not apply when: the switch-in is not actually safer, the active can take
  a clean KO now, or the switch gives up too much pressure.
- Example fixtures:
  - `chuck_poliwrath_vs_pidgeotto_ice_punch`
  - `pryce_slowking_vs_ampharos_ground_pivot`
  - `brock_golem_vs_vaporeon_explosion_question`
- Implementation target: switch preservation scoring and plan scoring.

### Scout Hidden Coverage Before Committing An Ace

- Status: developing
- Type: scout policy
- Rule: Hidden coverage suspicion can make probing, attacking once, or switching
  better than greedy setup before committing an ace.
- Applies when: the player staying in only makes sense if they have dangerous
  hidden coverage.
- Does not apply when: the threat is already revealed and the boss has a direct
  winning line.
- Example fixtures:
  - `clair_dragonair_vs_suicune_hidden_ice_beam`
  - `lance_dragonite_vs_suicune_champion_ace`
- Implementation target: public hidden-coverage risk scoring.

### Preserve Variety In Near-Tie Sacrifice Lines

- Status: developing
- Type: personality style
- Rule: If sacrifice, switch, and attack lines are genuinely close, the boss
  should preserve some variety instead of becoming deterministic.
- Applies when: both lines are defensible and source notes call out near-tie
  behavior.
- Does not apply when: one option is clearly forced by KO, public fail gate, or
  survival.
- Example fixtures:
  - `brock_golem_vs_vaporeon_explosion_question`
  - `morty_gengar_vs_kadabra_destiny_bond`
- Implementation target: final tie-break/randomization policy.

## Answered Teaching Notes

### Erika Victreebel vs Snorlax

- Fixture: `erika_victreebel_vs_snorlax_sleep_or_boost`
- Answer: Sleep Powder first. Even though it is inaccurate, landing sleep gives
  Victreebel the turn it needs to Swords Dance. After that, pressure with Sludge
  Bomb. If Snorlax wakes up, use Sleep Powder again only when Sleep Clause is
  legal.
- Extracted rule: Sleep can be the correct first move when it creates a setup
  turn that changes the damage race. The follow-up is bounded: setup once,
  attack, and re-sleep only after a legal wake state.

### Lance Yanma vs Lapras

- Fixture: `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`
- Answer: Same pattern as Erika. Sleep Powder first, then use the sleep turn to
  Quiver Dance, then attack with Giga Drain. Reapply Sleep Powder only after
  Lapras wakes up and only if Sleep Clause is legal.
- Extracted rule: Weak immediate damage plus dangerous hidden coverage can still
  favor sleep-first setup. The setup is not raw greed because sleep creates the
  turn that makes Quiver Dance safe enough to try.
