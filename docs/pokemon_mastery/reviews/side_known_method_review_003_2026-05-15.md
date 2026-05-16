# Side-Known Method Review 003 - 2026-05-15

Reviewed packets:
- `workspace/quick_tests/side_known_transfer_001_smogtours-gen2ou-924896_p1_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_002_smogtours-gen2ou-924543_p1_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_003_smogtours-gen2ou-923955_p2_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_004_smogtours-gen2ou-923104_p1_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_005_smogtours-gen2ou-885816_p1_2026-05-15.md`

## Combined Side-Known Sample

Decisions: 71.

Top-match: 39/71 = 54.9%.

Acceptable-match: 64/71 = 90.1%.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 60/71 = 84.5%.

Route-converting move chosen: 54/71 = 76.1%.

Branch-punish chosen: 44/66 = 66.7%.

Role-package update obeyed: 55/71 = 77.5%.

## Verdict

Flat, not progress proof.

Side-known prompting still looks better than pure spectator-public exact
training because acceptable-match, positive selection, and severe-error gates
are strong. But top-match is unchanged after another 20 fresh decisions, and
the hidden-info count is not back to zero. This triggers the plateau loop.

## Diagnosis

Most likely bottleneck: missing GSC route-timing subskills, not docs size.

The compact docs were small enough to use live. The new failure was not caused
by searching through too many cards; it was a local calculation gap in
Steelix-versus-Rest/Curse Snorlax. I recognized the owner and the reset loop,
but did not compute whether Curse or damage changed the next two turns.

Secondary bottleneck: the replay oracle is useful but noisy for exact attacks.
Rock Slide versus Earthquake can encode PP, Flying-type branches, or opponent
habits not fully visible from the public log. Those misses should still count
against top-match, but the training response should separate "same-role attack
ordering" from true route mistakes.

## Loop Change

Before more broad replay volume:

1. Add a compact Rest/setup timing rule to the live reset-loop card.
2. Run a focused drill on Rest-window setup timing: Steelix, CurseLax, Roar,
   and boosted attacker versus Rest user. Score it as regression only.
3. Resume side-known replay only after the drill, and stop again if the next
   packet repeats attack-versus-boost timing twice.

Do not count this as mastery progress. It is a method repair followed by a new
sample loop.
