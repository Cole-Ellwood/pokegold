"""Unified debugger umbrella for the Pokemon Gold hack.

Consolidates damage_debugger, boss_ai_debugger, boss_ai_preference,
pokemon_mastery, trace, and audit tools under one entry point.

Usage:
    python -m tools.debugger status          # list all tool entry-points
    python -m tools.debugger symbol resolve <name>
    python -m tools.debugger symbol render <bank>:<addr>
    python -m tools.debugger schema show
"""

__version__ = "0.1.0"
