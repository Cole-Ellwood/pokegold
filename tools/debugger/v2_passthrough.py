"""Dispatch for the self-contained "God" debugger verbs.

These verbs each ship as a standalone CLI with their own ``argparse`` inside
their own module. The front door delegates the remaining ``argv`` to the
module's ``main`` instead of registering them in the shared
``parsers``/``commands``/``formatters`` surface. That keeps the v1 Q&A-oracle
architecture untouched while the v2 capability verbs bolt on alongside it.

Harvested from the debugger-god integration; see
``docs/debugger_unification_plan.md`` for the harvest order and per-module
disposition.
"""

from __future__ import annotations

import importlib
from typing import Sequence

# verb -> module exposing ``main(argv) -> int``. Grows one cluster per harvest
# slice; keep it alphabetical within a slice for a stable ``--help`` listing.
V2_PASSTHROUGH_MODULES = {
    "clobbers": "tools.debugger.register_flow",
    "consequence": "tools.debugger.consequence",
    "save-state-lab": "tools.debugger.save_state_lab",
    "vram-diff": "tools.debugger.vram_diff",
    "vram-snapshot": "tools.debugger.vram_snapshot",
}


def delegate_to_module_main(module_name: str, argv: Sequence[str]) -> int:
    """Import ``module_name`` and run its ``main`` with ``argv``.

    Strips a leading literal ``--`` token: argparse REMAINDER keeps the
    separator when the parent CLI ends option parsing with ``--``, but the
    delegated module's own parser does not expect it.
    """
    args = list(argv or [])
    if args and args[0] == "--":
        args = args[1:]
    module = importlib.import_module(module_name)
    return int(module.main(args))
