# Counter-Handoff Transfer Review 001 - 2026-05-15

Reviewed packet:
`docs/pokemon_mastery/workspace/quick_tests/counter_handoff_transfer_001_smogtours-gen2ou-932564_2026-05-15.md`

## Verdict

Not progress. The packet hit 8/30 top and 22/30 acceptable with 0
severe/state/hidden/mechanics errors. That keeps the safety gates clean, but
top-match and branch obedience are too weak to claim improvement.

The compressed docs did help in two places:

- Lapras into Blissey was correctly identified as a Whirlpool/Perish package.
- Forretress correctly chose the missing Spikes layer before clearing hazards.

The wall is support-package recognition. I saw support moves, but did not
immediately re-score the role after Reflect, Charm, Pursuit, or Skarmory Curse
became public.

## Study Notes

Current GSC sources support this correction:

- Smogon's Umbreon material describes Charm as central to checking Curse
  sweepers and Pursuit as a real role, even though Umbreon is passive.
- The GSC sample-team breakdown describes Umbreon compressing FireLax check,
  Pursuit trapper, sleep absorber, and mixed wall roles; it also notes that
  Charm can help teammates pivot in.
- Smogon's Skarmory writeup lists Curse plus Whirlwind as part of the same
  package: Curse changes the physical-wall and endgame role, while Whirlwind
  remains the boost reset.
- Smogon GSC Spikes material and sample-team notes reinforce that stall teams
  need Rapid Spin and that defensive walls forced to Rest or take Spikes become
  exploitable. That explains why Starmie and Forretress kept appearing as
  counter-handoff owners.
- The local `support_handoff_after_job.md` already had the missing idea:
  screens and drops are often the first half of a route. The failure was that
  the live tiny card did not surface Reflect/Charm/Pursuit quickly enough.

Sources:

- https://www.smogon.com/gs/articles/gsc_threats
- https://www.smogon.com/forums/threads/umbreon-ou-revamp-qc-2-2-gp-2-2.3624491/
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/
- https://www.smogon.com/gs/articles/gsc_spikes

## Local Doc Update

`heuristic_core/rescore_after_reveal.md` now lists Reflect, Light Screen,
Charm, and Pursuit as package-changing reveals. This keeps the lesson in the
small live system without adding another card or reopening the archive.

## Next Rep

Run one fresh replay segment where a support move appears by turn 10. The answer
freeze should include:

`Public package reveal: ___ means this Pokemon's job is now ___, so the next owner is ___.`

Score whether support reveals improve top-match without sacrificing the clean
severe/hidden/state/mechanics gates.
