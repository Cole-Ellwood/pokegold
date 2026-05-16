# Side-Known Method Review 001 - 2026-05-15

Reviewed failed checks:
- `workspace/quick_tests/post_spin_branch_replication_transfer_001_smogtours-gen2ou-927928_2026-05-15.md`
- `workspace/quick_tests/one_cycle_converter_check_001_smogtours-gen2ou-927016_2026-05-15.md`
- `workspace/quick_tests/one_cycle_converter_check_002_smogtours-gen2ou-926958_2026-05-15.md`

## Combined Post-Repair Check

Decisions: 65.

Top-match: 26/65 = 40.0%.

Acceptable-match: 58/65 = 89.2%.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Verdict: regression/flat growth. Severe-blunder avoidance is still clean, but
that is only a gate. Exact top-match regressed badly versus the 38/69
post-Spikes/Spin sample, and the added one-cycle cards did not solve exact
move choice.

## Diagnosis

This is not primarily a docs-size problem. `active_context.md` and
`live_core.md` fit inside the intended compact caps.

The main method flaw is mismatched information. Pure spectator-public replay
prompts are useful for route-class calibration, but exact move choice often
depends on the advised side's private team and moves. In real play, that
information is known. In these prompts, it was hidden.

Examples:
- `927928`: Machamp Earthquake, Curse, and Rock Slide decisions depended on
  the user's own set.
- `927016`: Steelix handoff versus Cloyster Explosion depended on the user's
  hidden Steelix slot.
- `926958`: Cloyster preserving itself, Snorlax's Body Slam-only attacking
  package, and Starmie/Snorlax handoffs were side-known.

The second flaw is overcorrection. Because the last replay's miss was "did not
cash out," the next runs overpromoted Explosion into Starmie and Snorlax boards
where support delivery, status pressure, or own-team handoff was better.

## Training Change

Use two modes deliberately:

- Spectator-public mode: score route class, public-info discipline, branch
  naming, and severe errors. Do not use it as the main exact-top proof when
  own moves or hidden teammates matter.
- Side-known one-side mode: score exact move choice. Include only the advised
  side's reconstructed own roster and moves, keep opponent information public,
  and run only one advised side per replay to avoid cross-contamination.

## Implementation

`tools/pokemon_mastery/replay_turn_pause.py` now supports:

```text
python tools/pokemon_mastery/replay_turn_pause.py path/to/replay.log side-prompt --turn N --side p1
```

This is not perfect team-paste reconstruction; unused moves can be missing.
But it is a better proxy for real advice than guessing own moves from species
memory.

## Next Loop

The next countable progress loop should be one-side, side-known, fresh, and
focused on 12-18 decisions. Use the one-cycle card packet when cash-out, Rest,
phaze, or support jobs appear. If exact top remains flat there, the blocker is
not hidden own-team information, and the next method review should target
candidate ranking itself.
