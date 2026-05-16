# RestTalk Coverage Absorber Probe 002 - 2026-05-15

Source miss:
`workspace/quick_tests/side_known_transfer_004_smogtours-gen2ou-923104_p1_2026-05-15.md`

Mode: constructed nonblind regression from a known miss. This is not fresh
progress evidence.

Post-score sources:
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).

## Score Summary

Decisions: 4 constructed decisions.

Top-match: 4/4.

Acceptable-match: 4/4.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

## Probe

1. Zapdos 31% faces sleeping Snorlax with Rest, Sleep Talk, and Double-Edge
   revealed; Earthquake is a strong prior, not revealed. Top: Cloyster, not
   Gengar. Cloyster absorbs both the revealed Double-Edge roll and the
   strong-prior Earthquake roll; Gengar only wins the Double-Edge branch.
2. If Earthquake is then revealed and Cloyster is active, top: Surf. Do not
   switch back to the Ghost; keep pressure while the absorber still survives.
3. If all four Snorlax moves are public and Earthquake/Fire Blast are excluded,
   Gengar can become top. The missing coverage is now revealed absent, not
   assumed absent.
4. If the proposed absorber survives one Sleep Talk roll but loses the second,
   mark it as a temporary handoff, not a stable owner; rank the move that
   converts immediately or names the next fallback.

## Lesson

The fix is not "never use Ghost into sleeping Snorlax." The fix is: a sleeping
RestTalk attacker still has branches. Price revealed and strong-prior Sleep
Talk rolls before naming an absorber as the owner.
