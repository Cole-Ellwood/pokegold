# Explosion Absorber Resource Probe 001 - 2026-05-14

Mode: constructed policy regression. This is not a fresh replay score, not a
holdout, and not final-exam evidence.

Purpose: harden the severe miss from
`replay_turn_pause_035_unlabeled_hazard_cashout_transfer_smogtours-gen2ou-933816_2026-05-14.md`.
The repeated question is not "is Explosion likely?" but "which piece can
actually afford to absorb the one-time trade after future jobs are named?"

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_035_unlabeled_hazard_cashout_transfer_smogtours-gen2ou-933816_2026-05-14.md`

Web sources checked:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

Source note: Smogon's Explosion guide treats Explosion as a tactical route
trade, not generic damage. The Spikes article and Cloyster analysis make the
hazard-control version concrete: Cloyster can set Spikes, pressure spinners,
and later Explode, while Starmie and Forretress may still be the pieces that
keep hazards from deciding the game.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Resource-ranking hits: 6 / 6.

Worst-branch named: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0. Hidden teammates are phrased as conditionals
rather than known slots.

Measurement status: guided regression only. Count this as policy coverage, not
as unseen replay improvement.

## Extracted Checklist

When an opposing self-KO move is live:

1. Is the self-KO user already done with its support job, or does it still need
   Spikes, Toxic, Rapid Spin, phazing support, or direct chip?
2. Which of our pieces still have unique future jobs: spinner, Electric answer,
   Ground immunity, sleep-clause material, phazer, win condition, or sack?
3. Which piece has the lowest remaining agency if it absorbs the trade?
4. If we switch, does the incoming piece lose the exact job that makes the
   endgame playable?
5. If we stay, does the active piece become useful again after a wake, Rest,
   Sleep Talk, recovery, or support turn?
6. Is a Ghost, Rock, Steel, Protect, or low-value sack a real absorber, or does
   the exploder's ordinary attack punish that branch?

## Scenario 1 - Replay Miss: Let The Sleeping Anchor Absorb

Public state:

```text
Vanilla GSC. Our Snorlax is active at 100% asleep against opposing Cloyster at
100%. Our side has Spikes; opponent's side is clear. Our Starmie is 87% and has
Thunder Wave revealed but no Rapid Spin revealed yet. Our Forretress is unseen.
Opposing Cloyster has revealed Spikes. Opposing Raikou is paralyzed and alive;
opposing Zapdos is unrevealed.
```

Recommendation: stay with sleeping Snorlax and accept the Explosion trade.

Route reason: Snorlax currently has low agency while asleep, while Starmie and
Forretress may be the only remaining hazard-control and anti-Electric bridge.
Switching the likely spinner into Cloyster's obvious cash-out loses the pieces
that can still repair the board.

Worst branch: Cloyster does not Explode and uses Surf or Toxic while Snorlax
burns sleep, but that is still less damaging than donating Starmie or
Forretress to the trade before their jobs are known.

Score: pass.

## Scenario 2 - Preserve The Sleeping Anchor When It Is The Only Check

Public state:

```text
Vanilla GSC. Our Snorlax is active at 72% asleep against opposing Cloyster at
48%. Spikes are on our side. Our Starmie is fainted, but our Forretress at 64%
has Rapid Spin revealed. Opposing Zapdos is fainted; opposing last two are
Raikou at 82% and Skarmory at 70%. Snorlax is our only realistic Raikou answer
after it wakes.
```

Recommendation: switch Forretress into the Explosion branch if it survives the
ordinary Surf/Toxic line well enough; otherwise use the lowest-value sack.

Route reason: this is the exception to Scenario 1. The sleeping Snorlax is not
spent material; it is the future Electric answer. Forretress has a support job,
but if Starmie is already gone and the Raikou endgame depends on Snorlax,
Snorlax cannot be the absorber by default.

Worst branch: Cloyster Surfs or Toxics on the Forretress switch and keeps the
hazard route alive, so Forretress must be able to still Spin or force Cloyster
after the switch.

Score: pass.

## Scenario 3 - Do Not Preserve A Spinner By Losing The Win Condition

Public state:

```text
Vanilla GSC. Our Marowak is active at 88% after forcing paralyzed Raikou out.
Opposing Cloyster is at 66%, has revealed Spikes and Explosion, and Spikes are
on our side. Our Starmie is 100% with Rapid Spin revealed, but Marowak is the
only Pokemon that can beat the opponent's last Raikou and Tyranitar pair.
```

Recommendation: switch Starmie or another lower-value absorber into the
Explosion branch; do not leave Marowak in to protect Starmie abstractly.

Route reason: hazard removal matters, but the actual win route is Marowak
surviving for the Electric/Rock endgame. If Cloyster cashes out into Marowak,
the route collapses; Starmie can still be spent if removing or absorbing the
trade preserves the only cleaner.

Worst branch: Cloyster uses Toxic or Surf into Starmie, making later Rapid Spin
harder. That is acceptable only because losing Marowak is worse.

Score: pass.

## Scenario 4 - Cash Out The Support User Into The Immediate Threat

Public state:

```text
Vanilla GSC. Our Forretress is active at 94% against opposing Zapdos at 100%.
Our side has Spikes. Our Starmie is healthy in back and can remove Spikes later
if it gets in. Zapdos is the opponent's remaining pressure piece, and our
normal Electric answers are gone or asleep.
```

Recommendation: Explosion with Forretress, confidence medium-high.

Route reason: Forretress can spin, but spinning leaves Zapdos active with the
better board. If Starmie can still handle hazard removal later, Forretress's
highest-value job is to trade into the immediate route threat.

Worst branch: Zapdos switches to a Rock, Steel, or Ghost-like absorber, or
Forretress misses the actual route threat because the opponent preserves
Zapdos. If that absorber is likely and costly, use Spikes/Spin or a pivot
instead.

Score: pass.

## Scenario 5 - Use The Low-Pressure Spin Window Before Damage

Public state:

```text
Vanilla GSC. Our Starmie is active at 75% against opposing Machamp at 54%.
Spikes are on our side. Starmie has Thunder Wave revealed; Rapid Spin is
available from our team sheet. Machamp has revealed Cross Chop only and just
entered to punish Marowak.
```

Recommendation: Rapid Spin, confidence medium.

Route reason: the board is not only "attack Machamp." Before Machamp boosts or
reveals Starmie-targeting coverage, this is a low-pressure window to clear the
entry tax and preserve Starmie/Marowak mobility.

Worst branch: Machamp Curses or reveals coverage while Starmie only chips with
Rapid Spin. That branch must be priced, but it is often still better than
letting Spikes keep constraining every Electric-answer pivot.

Score: pass.

## Scenario 6 - Public Conditional: Name The Absorber Without Claiming Preview

Public state:

```text
Spectator-public GSC replay. Our Starmie is active at 81% against paralyzed
Raikou at 100%. Spikes are on our side. Starmie has Thunder Wave revealed and
Rapid Spin is possible but not public. Raikou has revealed Thunder. Our bench
is not fully public.
```

Recommendation: "Ground immune-to-Thunder answer if available; otherwise Rapid
Spin or a Starmie pivot depending on known own-team moves." Do not state the
hidden Ground as fact in spectator-public mode.

Route reason: the public state screams for an Electric immunity, but no Team
Preview means the exact slot is conditional unless the side-known team sheet is
available. The recommendation should still rank the conditional first because
it is the route if the piece exists.

Worst branch: forcing Starmie to act because the Ground is not public loses the
natural answer; claiming the Ground is known would be hidden-information abuse.

Score: pass.

## Next Rep

Run a fresh replay segment where a support Pokemon can either remove hazards,
cash out with Explosion, or preserve itself. Stop at the first self-KO threat
and score the absorber choice before revealing the turn.
