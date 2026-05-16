# Compounding Loop Pgoal Spec

These four files are the checked-in source of truth for the durable
/pgoal that operates the Compounding Loop. A fresh Claude session that
wants to (re-)arm the loop reads these files instead of needing to
retype the spec.

| File | Role |
| --- | --- |
| `objective.txt` | The durable objective text (the loop spec a continuation sees every turn) |
| `criteria.txt` | The six success criteria, tagged [v1]..[v5] + [manual] |
| `constraints.txt` | Hard constraints the loop must respect |
| `verify.txt` | The five verifier commands |

## To (re-)arm the loop in a fresh Claude session

Easiest — say to Claude: "arm the pokemon mastery pgoal".

Equivalently:

```bash
python tools/pokemon_mastery/arm_pgoal.py
```

The wrapper reads these four files and shells out to the /pgoal harness.

Fully manual:

```bash
python ~/.claude/skills/pgoal/scripts/pgoal.py set \
  --objective "$(cat tools/pokemon_mastery/pgoal_spec/objective.txt)" \
  --phase implementation \
  --criteria "$(cat tools/pokemon_mastery/pgoal_spec/criteria.txt)" \
  --constraints "$(cat tools/pokemon_mastery/pgoal_spec/constraints.txt)" \
  --verify "$(cat tools/pokemon_mastery/pgoal_spec/verify.txt)" \
  --long-run \
  --continuation-style adaptive \
  --full-prompt-every-iterations 25 \
  --assume-defaults
```

The pgoal state is **per-worktree-path** (project hash). Re-arming in
the main repo path creates a separate slot from the worktree slot;
the case library is per-checkout, so both reads/writes hit the same
case_library files via git.

## To pause the loop without losing state

```bash
python ~/.claude/skills/pgoal/scripts/pgoal.py pause
```

Resume with `pgoal.py resume`. Clear with `pgoal.py clear` (destructive
to pgoal state; the case library is untouched).
