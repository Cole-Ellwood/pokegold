# AGENTS.md — standing rules for Codex (GPT-6 Astra) workers in this repo

Codex reads this file automatically. Each job you run comes with a brief file
(`.local/<job>-brief.md`) that says WHAT to build; this file is the HOW that
never changes. The brief wins on scope; this file wins on rules.

## What this project is

A Pokémon Gold ROM hack on the pret/pokegold disassembly (Sharp SM83, RGBDS).
The design lead (Cole) does not code and never sees your chat; the Claude
lead reads your report file and reviews your diff. Read `CLAUDE.md` first,
then `docs/asm_authoring_guide.md` §0 and §3 before touching any `.asm`, and
`docs/agent_navigation/gen2_vs_modern_mechanics.md` before any mechanics
claim (this is Gen 2: split by type, no abilities, DVs 0-15).

## How much freedom you have

The brief tells you WHAT to build and what "done" means; the approach is
yours. Anything in a brief marked as a diagnosis, a suggested route or "I'd
try" is a starting point, not a script. If you find a better way, a simpler
one, or a bug the brief did not know about, take the better route and fix the
bug, and say plainly in the commit message and the report what you changed
and why. Only the constraints below, the gates, and explicit design-lead
rulings are fixed.

## Code standard (the lead reviews for this)

Prefer the smallest change that works: fewest moving parts, reuse what exists
before inventing a helper, delete what you replace. No play-by-play comments
inside routines; a comment says why, not what the next instruction does. No
redundant loads, saves or calls (a helper that loads its own pointer does not
need the caller to load it). No copies of a routine that already exists in
the same bank. Fixtures are declarative rows, not new frameworks, unless the
existing harness genuinely cannot reach the behaviour. A diff that removes
lines is as welcome as one that adds them.

## Rules that never bend

- Boss AI uses public information only: the player's active species, level,
  types, HP, status, stat stages, revealed moves, and the boss's own party.
  Never `wBattleMonMoves`, `wBattleMonPP`, `wBattleMonItem`, the
  `wBattleMon*` stat words, `wPlayer{Attack,Defense,Speed,SpAtk,SpDef,Stats}`,
  `wPartyMon*`, `wPartyCount`, `wCurPlayerMove`, `wBattlePlayerAction`, joypad
  or menu state. `tools/audit/check_boss_ai_no_cheat.py` enforces the symbols;
  the rule is broader than the audit.
- Register contract: `farcall`/`callfar` destroys the caller's `hl` BEFORE the
  target runs and the caller's `a` AFTER (a becomes the target's exit `c`); a
  plain `call`/`jp` reaches only the same bank or ROM0 (banks are in
  `pokegold.sym`). A routine that changes which registers it preserves can
  break a caller three frames away; say so in the commit when you change one.
- No new WRAM bytes in the boss AI reserve without the lead's approval (the
  trace build has zero free). `ram/` offsets are the save format.
- Never hand-edit `docs/generated/*`, `*.gbc`, `*.sym`, `*.map`, `*.o`.
- Bank 0e ("Enemy Trainers") is tight; report its free-byte figure from the
  `Enemy Trainers` row of `docs/generated/dev_index.md` before and after.
- Fixture rule: pin every branch at BOTH polarities; a collapsed branch still
  passes a one-sided test. Fixtures are declarative rows in
  `tools/boss_ai_fixtures/cases.py` (`python -m tools.boss_ai_fixtures --list`).
  When a change fixes behaviour, run your rows against the pre-change ROM the
  brief names and record which rows fail there (the red proof).
- Windows Python opens files as cp1252: always pass `encoding="utf-8"`.
- Write files with LF line endings (the repo is LF; a CRLF rewrite turns a
  ten-line change into a whole-file diff). Pass `newline="\n"` from Python.

## Build and gates

Build only through WSL, from your worktree, with the Windows RGBDS binaries:

```
wsl -e bash -lc 'cd "/mnt/c/<your worktree path>" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold_ai_reference.gbc pokegold.gbc'
python scripts/generate_dev_index.py --rom pokegold
```

Never rebuild while a fixture suite is running. Python scripts run as files
need `PYTHONPATH=.`. Gates, all green before "done":

- `python -m tools.boss_ai_fixtures --rom pokegold --suite production`
  (must end `PASS: all N boss-AI decision-path fixtures hold`)
- `python tools/audit/check_boss_ai_no_cheat.py`, `check_cross_bank_call.py`,
  `check_farcall_hl_clobber.py`, `check_farcall_a_clobber.py`,
  `check_boss_ai_memory_budget.py`, `check_boss_ai_gating.py`,
  `check_boss_ai_policy_contract.py`
- reference-only code (`fast_*.asm`, `action_*.asm`, `public_replies.asm`,
  `joint_action.asm`): `PYTHONPATH=. python tools/boss_ai_fixtures/fast_reference.py --prototype`
  must stay exact, and the game ROM SHA1 must not change
- last: `python tools/audit/check_release_smoke.py`

## Git

Work only in your worktree and branch. Small themed commits with
`git -c user.name="Codex" -c user.email="codex@openai.com" commit`; the
message states the evidence (fixture names, red/green on old vs new ROM, suite
count, ROM SHA1 before/after). Never push, never merge, never touch `master`,
never delete more than half of any file (a pre-commit hook refuses it), never
use `git stash`.

## Talking to the lead (you cannot message; files are the channel)

- Progress: after each task or gate, append one line to
  `.local/<job>-status.md` (`HH:MM task 2 done, suite 531/531`). The lead
  polls this file.
- Blocked on a decision only a human can make (a taste call, a save-format
  change, a gate that stays red after two honest attempts): write the
  question and your recommendation to `.local/<job>-blocked.md`, commit what
  is green so far, and stop. The lead answers by editing the brief and
  resuming you (`codex exec resume --last`).
- Done: write `.local/<job>-report.md` (failures and anything unproven
  first, then commits, fixtures, red/green evidence, suite count, bank
  bytes, ROM SHA1 before/after) and print it as your final message.
