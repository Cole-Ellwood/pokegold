from __future__ import annotations

import sys

from tools.boss_ai_preference.data import PreferenceDataError
from tools.debugger.command_metadata import read_only_refusal_for

from .parsers import build_parser


def _strip_global_read_only(argv: list[str] | None) -> tuple[bool, list[str]]:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "--read-only":
        return True, argv[1:]
    return False, argv


def main(argv: list[str] | None = None) -> int:
    read_only, argv = _strip_global_read_only(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if read_only:
            refusal = read_only_refusal_for(f"boss-ai:{args.command}", argv)
            if refusal is not None:
                raise PreferenceDataError(refusal)
        return args.func(args)
    except PreferenceDataError as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
