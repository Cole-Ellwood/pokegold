# Side-Known Method Review 002 - 2026-05-15

Reviewed packets:
- `workspace/quick_tests/side_known_transfer_001_smogtours-gen2ou-924896_p1_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_002_smogtours-gen2ou-924543_p1_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_003_smogtours-gen2ou-923955_p2_2026-05-15.md`
- `workspace/quick_tests/side_known_transfer_004_smogtours-gen2ou-923104_p1_2026-05-15.md`

## Combined Side-Known Sample

Decisions: 51.

Top-match: 28/51 = 54.9%.

Acceptable-match: 46/51 = 90.2%.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 42/51 = 82.4%.

Route-converting move chosen: 38/51 = 74.5%.

Branch-punish chosen: 31/48 = 64.6%.

Role-package update obeyed: 39/51 = 76.5%.

## Verdict

Mixed, not progress proof.

Side-known prompting is probably better than pure spectator-public exact-move
training: acceptable-match and positive route metrics are strong, and the
RestTalk/absorber miss from packet 002 did not recur after the regression
probe. But top-match is just under the gate, the sample is only 51 decisions,
and packet 004 reintroduced one hidden-info error by ignoring a strong-prior
Sleep Talk Earthquake branch into Gengar.

## What Changed

- Own-team and own-move noise decreased.
- Baton Pass and screen-package routes became easier to classify.
- RestTalk action autopilot was corrected in the constructed probe and did not
  repeat as the exact same mistake in packets 003-004.

## Remaining Bottleneck

The live system still mishandles absorber switches into sleeping RestTalk
attackers. It now knows Sleep Talk is not automatic, but it must also ask:

```text
What does each revealed or strong-prior Sleep Talk roll do to the proposed
absorber?
```

Ghosts, Rock/Steel resists, Cloyster, and sleeping Snorlax are all different
answers depending on whether Double-Edge, Earthquake, Fire Blast, Lovely Kiss,
Curse, or Rest is public or strongly implied.

## Next Loop

Before more broad side-known replay volume, run one small RestTalk coverage
regression or one fresh side-known packet that stops immediately if it repeats
the Ghost/absorber coverage miss. If that passes, collect another 30-40 fresh
side-known decisions before making any trend claim.
