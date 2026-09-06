from __future__ import annotations

import sys
from typing import Sequence

from .command_metadata import read_only_refusal_for
from .parsers import build_parser, command_parsers


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
    parser = build_parser()
    command = command_parsers(parser).get(argv[0]) if argv else None
    standalone = command is not None and command.get_default("command_module")
    if standalone:
        # Standalone commands historically refuse read-only requests even
        # before parsing/help; shared commands validate arguments first.
        if read_only:
            refused = _refuse_read_only(command.get_default("command_id"), argv)
            if refused:
                return refused
        # The former standalone dispatch accepted a leading separator.
        if argv[1:2] == ["--"]:
            del argv[1]
    args = parser.parse_args(argv)
    if read_only and not standalone:
        refused = _refuse_read_only(args.command_id, argv)
        if refused:
            return refused
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
