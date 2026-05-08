# Boss AI Preference Lab

Version A of BOSSAI-004: a small preference-labeling side app for public-info
boss battle states.

Mechanics reminder for future scoring work: read
`docs/agent_navigation/gen2_vs_modern_mechanics.md` before turning preference
notes into type-chart claims. In particular, Magnitude is neutral into Miltank;
the Whitney Rollout label is about bad lock-in against meaningful damage, not
super-effective Ground damage.

The default browser flow is pairwise: compare the current baseline boss action
against a plausible alternative, then choose which option uses public info,
keeps tempo, creates scary pressure, or fits the boss style. The older
single-action labels remain supported for explicit audit notes.

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
python -m tools.boss_ai_preference label --fixture-id clair_dragonite_vs_suicune_hidden_ice_beam --action-id switch_kingdra --label best --rank 1 --note "Preserves Dragonite against public Ice Beam risk."
```

Record a pairwise preference without the browser:

```powershell
python -m tools.boss_ai_preference prefer --fixture-id bugsy_scyther_vs_quilava_fire_pressure --action-a-id move_swords_dance --action-b-id move_wing_attack --choice b_better --preferred-action-id move_wing_attack --action-tag move_swords_dance:too_greedy --action-tag move_wing_attack:keeps_tempo --note "Fire pressure is already public."
```

Saving the same fixture/action pair again replaces the older row, even if the
left/right display order changed. This keeps the solo review file focused on
your latest judgment.

Write reports:

```powershell
python -m tools.boss_ai_preference report
python -m tools.boss_ai_preference threat-report
```

Default report outputs:
- `audit/boss_ai_preference/latest_report.md`
- `audit/boss_ai_preference/latest_report.json`
- `audit/boss_ai_preference/threat_availability_report.md`
- `audit/boss_ai_preference/threat_availability_report.json`

Threat availability report limits are explicit. It parses wild grass,
Surf-gated water, fishing tables by rod tier, simple `givepoke` gifts/prizes,
listed static encounters, level-up moves, base-stat TM/HM compatibility, direct
TM map rewards, and the Day-Care voucher tutor. It does not yet fully
route-model breeding, trades, roaming RNG, or prerequisite-heavy statics.

## Scope

This tool does not optimize weights, run self-play, or edit ROM behavior. Its
job is to collect durable user taste preferences that can later drive the boss
AI debugger, scorer, and optional optimizer.
