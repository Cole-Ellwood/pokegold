# Debugger User Guide

Quick-reference for the unified debugger (`python -m tools.debugger`).

## Getting started

```
python -m tools.debugger status          # list all tools and build artifacts
python -m tools.debugger selftest        # run all 29 component + integration tests
```

## Symbol service

```
python -m tools.debugger symbol resolve wBattleMonHP
python -m tools.debugger symbol render 01:4000
```

## Battle analysis

Metamorphic relations check damage invariants against the real oracle
(tools/damage_debugger/oracle.py). Battle fuzz uses Hypothesis
RuleBasedStateMachine with oracle-backed damage calculation.

```
python -m tools.debugger battle damage CROBAT:44 ALAKAZAM:44 WING_ATTACK --explain
python -m tools.debugger metamorphic --count 50
python -m tools.debugger fuzz --examples 200
```

## Static analysis

```
python -m tools.debugger static analyze
python -m tools.debugger static clobber-summary BattleCommand_DamageCalc
python -m tools.debugger static bank-pressure --threshold 256
python -m tools.debugger static save-lock --generate
```

## Save-state lab

Decodes VBA-M .sgm save states (gzip + heuristic WRAM bank scanning)
and PyBoy states. Cross-format diff compares field by field.

```
python -m tools.debugger savelab decode path/to/save.sgm
python -m tools.debugger savelab diff state_a.sgm state_b.state
```

## Stress testing

Tournament loads all trainers from data/trainers/parties.asm. With
`--emulate`, each match boots the ROM in PyBoy and runs the battle.
Without `--emulate`, reports structural data only (dry run).

```
python -m tools.debugger tournament --dry-run
python -m tools.debugger tournament --emulate
python -m tools.debugger bisect --scenario physical_no_items --good abc123 --bad HEAD
```

## Hypothesis tracker

JSONL-backed hypothesis tree with citation grounding. The grounder
validates that cited file:line references actually exist in the repo.

```
python -m tools.debugger hypothesis add "wCurDamage clobbered by farcall hl expansion"
python -m tools.debugger hypothesis list --status open
python -m tools.debugger hypothesis tree
```

## Web UI

Requires `pip install fastapi uvicorn`. Serves a dark-themed dashboard
with symbol lookup, run browser, and API endpoints.

```
python -m tools.debugger web --port 8765
```

Then open `http://127.0.0.1:8765` in a browser.

API endpoints:
- `GET /api/status` - ROM and symbol stats
- `GET /api/symbols/{name}` - resolve a symbol
- `GET /api/damage?level=50&bp=60&atk=100&dfn=80` - oracle damage calc
- `GET /api/runs` - list experiment runs

## MCP tools (for Claude integration)

```
python -m tools.debugger mcp list
python -m tools.debugger mcp call read_symbol name=wBattleMonHP
```

## DAP / VS Code debugging

The DAP server connects to PyBoy for real instruction stepping when a
ROM is available. Without a ROM, it runs in protocol-testing mode with
local register state.

Add to `.vscode/launch.json`:

```json
{
    "type": "gbc-debug",
    "request": "launch",
    "name": "Debug Pokemon Gold",
    "program": "${workspaceFolder}/pokegold.gbc"
}
```

The DAP server runs over stdio:

```
python -m tools.debugger.presentation.dap
```

## Viewers (live emulator state)

All viewers support `from_session(debug_session)` for live PyBoy state
capture, plus `from_bytes(raw_data)` for offline analysis:

- **VRAM viewer** - 2bpp tiles, BG/window maps, tilemap diff
- **OAM viewer** - 40 sprite entries with position, tile, flags
- **Palette viewer** - 8 BG + 8 OBJ palettes, GBC 15-bit color decode
- **Audio scope** - 4 audio channels, wave RAM, music state
- **Map tracer** - named event flags from constants/event_flags.asm
