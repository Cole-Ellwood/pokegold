from __future__ import annotations

import sys
from typing import Sequence

from .parsers import build_parser
from .v2_passthrough import V2_PASSTHROUGH_MODULES, delegate_to_module_main


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    # Self-contained v2 ("God") verbs own their argparse; delegate before the
    # shared parser runs so their --help and flags reach the module cleanly.
    if argv and argv[0] in V2_PASSTHROUGH_MODULES:
        return delegate_to_module_main(V2_PASSTHROUGH_MODULES[argv[0]], argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
