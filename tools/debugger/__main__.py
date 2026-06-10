from __future__ import annotations

import sys
from typing import Sequence

from .command_metadata import read_only_refusal_for
from .parsers import build_parser
from .v2_passthrough import V2_PASSTHROUGH_MODULES, delegate_to_module_main


def _strip_global_read_only(argv: list[str]) -> tuple[bool, list[str]]:
    if argv and argv[0] == "--read-only":
        return True, argv[1:]
    return False, argv


def _refuse_read_only(command_id: str, command_argv: Sequence[str]) -> int:
    refusal = read_only_refusal_for(command_id, command_argv)
    if refusal is None:
        return 0
    sys.stderr.write(refusal + "\n")
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    read_only, argv = _strip_global_read_only(argv)
    # Self-contained v2 ("God") verbs own their argparse; delegate before the
    # shared parser runs so their --help and flags reach the module cleanly.
    if argv and argv[0] in V2_PASSTHROUGH_MODULES:
        if read_only:
            refused = _refuse_read_only(f"debugger-v2:{argv[0]}", argv[1:])
            if refused:
                return refused
        return delegate_to_module_main(V2_PASSTHROUGH_MODULES[argv[0]], argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    if read_only:
        refused = _refuse_read_only(f"debugger:{args.command}", argv)
        if refused:
            return refused
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
