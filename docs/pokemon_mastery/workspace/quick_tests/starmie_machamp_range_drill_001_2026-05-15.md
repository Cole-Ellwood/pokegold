# Starmie Machamp Range Drill 001 - 2026-05-15

Mode: constructed nonblind regression from packet 009. This is not fresh
progress evidence.

Sources reviewed:
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).
- Smogon Forums, [GSC OU Starmie](https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/).

## Score Summary

Scenarios: 4.

Route-intent match: 4/4.

Exact-move match: 4/4.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Verdict: regression pass only.

## Scenarios

1. Starmie at 44% faces Machamp at 71% with Cross Chop revealed and Hidden
   Power strongly prior. Psychic does not KO. Top: Recover.
2. Starmie at high HP faces Machamp at 71%. Psychic into the 2HKO is top if
   Starmie survives the return hit and can Recover next turn.
3. Starmie at 44% faces Machamp at 25%. Psychic is top because it removes the
   route piece before Hidden Power can matter.
4. Starmie at 44% faces Machamp at 71%, but Zapdos or Exeggutor can enter
   without losing the route. Top: handoff if Recover no longer preserves the
   Starmie job.

## Reusable Rule

Coverage is not conversion unless it changes the next forced choice. A low
defensive route piece must check KO/survival before attacking.
