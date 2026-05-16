# Trap Pass Quarantine 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-536736
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-536736.log

Mode: spectator public.

Status: quarantined mechanics packet, not counted in the current-GSC fresh
progress sample.

Quarantine reason: post-score source check found that current Smogon GSC OU
rules ban Mean Look/Spider Web + Baton Pass. This historical replay used
Spider Web + Baton Pass, so it can teach trap/Encore state tracking but should
not be used to measure current singles-advisor strength.

Post-score source:
- Smogon official GSC OU vote thread, July 10, 2022: the outcome line says
  Mean Look/Spider Web + Baton Pass is now banned from GSC OU.

Contamination control: turns 1-12 were revealed only through the helper before
freezing each answer. Turn 8-11 p1 full-paralysis no-action decisions were
excluded because the chosen move was not logged.

## Score Summary

Scored decisions: 20.

Top-match: 6/20.

Acceptable-match: 11/20.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 16/20.

Route-converting move chosen: 13/20.

Branch-punish chosen: 10/20.

Role-package update obeyed: 11/13 relevant package decisions.

Selection validity error: 1. The replay was legal historically but not current
GSC OU after the 2022 TrapPass ban.

## Turn Notes

- Turn 1: Zapdos into Smeargle was treated too much as Spore/pass; p2 instead
  made the Snorlax Electric-absorber handoff immediately.
- Turn 2-4: Snorlax revealed Ice Beam and froze Zapdos; the correct public job
  update was `Electric absorber + coverage lure`, then `frozen Zapdos is no
  longer the pressure owner`.
- Turn 5: I over-anchored the unrevealed Spore branch and wanted to move frozen
  Zapdos in as status absorber. Actual Smeargle revealed Spider Web while
  Forretress got Spikes. This is the hidden-info error.
- Turn 6-12: Spider Web + Encore + Thunder Wave + Baton Pass made a trap-pass
  package. The helper did not display trap/Encore state in later prompts, so
  the state had to be manually carried. I did carry it, but I under-ranked the
  repeated Thunder Wave stalling sequence before the final Baton Pass to
  Jolteon.

## Reusable Lesson

Replay selection is part of the training method. Historical tournament replays
can contain lines that are no longer legal in current GSC OU. If a current rule
or ban changes the legality of the route being trained, quarantine the packet as
mechanics study and do not compare its score to the current progress baseline.

Trap-pass state rule for mechanics drills:

```text
After Spider Web/Mean Look plus Encore, manually carry trap and Encore state if
the prompt omits it. Rank the denial move before generic hazards, but also check
whether faster Encore can prevent the denial move from happening.
```
