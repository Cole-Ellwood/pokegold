# Boss AI Preference Lab

Version A of BOSSAI-004: a small preference-labeling side app for public-info
boss battle states.

Mechanics reminder for future scoring work: read
`docs/agent_navigation/hack_mechanics_reference.md` and
`docs/agent_navigation/gen2_vs_modern_mechanics.md` before turning preference
notes into type-chart claims. In particular, Magnitude is neutral into Miltank;
Dragon's Majesty turns a Dragon attacker's type-chart immunity result into a
resistance for damage and no-item Boss AI matchup scoring; the Whitney Rollout
label is about bad lock-in against meaningful damage, not a super-effective
Ground hit.

The default browser flow is now Coach Mode: pick a generated 3-5 turn plan card
or mark that the best plan is missing. The older pairwise and single-action
flows remain available under the Data tab for direct move labels and audit notes.

Reason tags are attached to each action separately. For example, in Falkner's
`Gust` versus `Sand Attack` fixture, you can tag `Gust` as `too_passive` and
`Sand Attack` as `reduces_risk` before saving the preference.

Attacking moves also show a rough damage estimate as a percentage of the target's
max HP. These estimates are review aids, not exact simulator rolls; they use
public fixture state and the damage debugger's oracle for type matchups, weather,
type passives, and visible attacker/defender item boosts.

The battle-state pane also shows relevant incoming player threats. These come
from source-derived level-up/TM/HM data, conservative boss checkpoints, revealed
fixture moves, and rough damage estimates. The app keeps legality separate from
likelihood with coarse buckets only: `0%`, `25%`, `50%`, `75%`, and `99%`.
Seen-party switch threats also get a separate switch-fit check from revealed
boss damage, so a likely move on a bad switch-in does not look like immediate
active pressure.

Coach snapshots also attach source-derived boss team rows from
`data/trainers/parties.asm`, so the boss side can show its own full party,
items, and move sets while the player side remains public-info bucketed.

## Commands

Validate fixtures and labels:

```powershell
python -m tools.boss_ai_preference validate
```

Start the local review UI:

```powershell
python -m tools.boss_ai_preference serve --host 127.0.0.1 --port 8765
```

Record a label without the browser:

```powershell
python -m tools.boss_ai_preference label --fixture-id clair_dragonair_vs_suicune_hidden_ice_beam --action-id switch_kingdra --label best --rank 1 --note "Pivots to Kingdra against public Ice Beam risk."
```

Record a pairwise preference without the browser:

```powershell
python -m tools.boss_ai_preference prefer --fixture-id bugsy_scyther_vs_quilava_fire_pressure --action-a-id move_swords_dance --action-b-id move_wing_attack --choice b_better --preferred-action-id move_wing_attack --action-tag move_swords_dance:too_greedy --action-tag move_wing_attack:keeps_tempo --note "Fire pressure is already public."
```

Saving the same fixture/action pair again replaces the older row, even if the
left/right display order changed. This keeps the solo review file focused on
your latest judgment.

## Label quality

After roster or moveset changes, refresh fixtures before treating labels as
training signal. Keep compared actions legal for the current boss moveset, and
prefer paired examples when a move is conditional: one fixture where the move is
good and one where it is bad. If the real lesson is upstream team selection or
ace timing rather than the current move choice, use `needs_context` and say so
in the note.

Write reports:

```powershell
python -m tools.boss_ai_preference report
python -m tools.boss_ai_preference threat-report
python -m tools.boss_ai_preference feature-report
python -m tools.boss_ai_preference active-queue
python -m tools.boss_ai_preference plan-queue
python -m tools.boss_ai_preference trajectory-report
python -m tools.boss_ai_preference trajectory-regress
python -m tools.boss_ai_preference coach-report
python -m tools.boss_ai_preference generate-counterfactuals --dry-run
python -m tools.boss_ai_preference lesson-report
python -m tools.boss_ai_preference fit-model
python -m tools.boss_ai_preference propose
python -m tools.boss_ai_preference final-report
```

`lesson-report`, `fit-model`, and `propose` include Coach Mode trajectory rows
by default. Use `--no-include-trajectories` for a legacy action-only check.

`trajectory-regress` grades the current Python scorer against trajectory
preference labels. First-move comparison with a cumulative boss-action
tiebreaker when both plans share their turn-1 action. Static — does not
simulate state evolution. Writes `audit/boss_ai_preference/trajectory_regression_report.json`
with `--json-out`. Default threshold 0.80; exits non-zero on failure so it
can be wired into CI gates. Pairs with the pairwise-only
`python -m tools.boss_ai_debugger regress`.

`--canonical-scope <scope>` filters labels by `public_info_scope`, so older
labels written under a stale reasoning frame don't drag down the metric
against a scorer whose canonical frame has moved. Example: the iter-5
pairwise label for `clair_dragonair_vs_suicune_hidden_ice_beam` recorded
that the canonical scope for this loop is `public_plus_common_meta`
(Bayesian inference over revealed-moves-plus-meta priors). The legacy
trajectory labels for that fixture sit at `public_only` and disagree with
the now-Bayesian scorer; with `--canonical-scope public_plus_common_meta`
they are skipped under `non_canonical_scope` and only the canonical-scope
labels grade the scorer.

Default report outputs:
- `audit/boss_ai_preference/latest_report.md`
- `audit/boss_ai_preference/latest_report.json`
- `audit/boss_ai_preference/threat_availability_report.md`
- `audit/boss_ai_preference/threat_availability_report.json`
- `audit/boss_ai_preference/feature_report.md`
- `audit/boss_ai_preference/feature_report.json`
- `audit/boss_ai_preference/active_queue.md`
- `audit/boss_ai_preference/active_queue.json`
- `audit/boss_ai_preference/plan_queue.md`
- `audit/boss_ai_preference/plan_queue.json`
- `audit/boss_ai_preference/trajectory_report.md`
- `audit/boss_ai_preference/trajectory_report.json`
- `audit/boss_ai_preference/coach_report.md`
- `audit/boss_ai_preference/coach_report.json`
- `audit/boss_ai_preference/final_report.md`
- `audit/boss_ai_preference/final_report.json`
- `audit/boss_ai_preference/counterfactuals.md`
- `audit/boss_ai_preference/counterfactuals.json`
- `audit/boss_ai_preference/lesson_report.md`
- `audit/boss_ai_preference/lesson_report.json`
- `audit/boss_ai_preference/reward_model_report.md`
- `audit/boss_ai_preference/reward_model_report.json`
- `audit/boss_ai_preference/proposals.md`
- `audit/boss_ai_preference/proposals.json`

Threat availability report limits are explicit. It parses wild grass,
Surf-gated water, fishing tables by rod tier, simple `givepoke` gifts/prizes,
listed static encounters, level-up moves, base-stat TM/HM compatibility, direct
TM map rewards, and badge-gated map access. It does not yet fully route-model
breeding, trades, roaming RNG, or prerequisite-heavy statics.

## Scope

V2 adds active-query ranking, portable lesson reports, counterfactual fixture
families, a tiny offline pairwise model over readable features, and a multi-turn
Coach UI for plan and trajectory labels. These tools produce review reports and
candidate proposals only. They do not auto-edit ROM behavior; source changes
remain manual and auditable.

The Coach UI implementation is tracked in
`docs/boss_ai_multiturn_coach_ui_plan.md`.
