# Debugger User Guide

Quick-reference for the unified debugger (`python -m tools.debugger`).

## Getting started

```
python -m tools.debugger status          # list all tools and build artifacts
python -m tools.debugger selftest        # run all component self-tests
```

## Symbol service

```
python -m tools.debugger symbol resolve wBattleMonHP
python -m tools.debugger symbol render 01:4000
```

## Battle analysis

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

```
python -m tools.debugger savelab decode path/to/save.sgm
python -m tools.debugger savelab diff state_a.sgm state_b.state
```

## Stress testing

```
python -m tools.debugger tournament --dry-run
python -m tools.debugger bisect --scenario physical_no_items --good abc123 --bad HEAD
```

## Hypothesis tracker

```
python -m tools.debugger hypothesis add "wCurDamage clobbered by farcall hl expansion"
python -m tools.debugger hypothesis list --status open
python -m tools.debugger hypothesis tree
```

## Web UI

```
python -m tools.debugger web --port 8765
```

Then open `http://127.0.0.1:8765` in a browser.

## MCP tools (for Claude integration)

```
python -m tools.debugger mcp list
python -m tools.debugger mcp call read_symbol name=wBattleMonHP
```

## DAP / VS Code debugging

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
