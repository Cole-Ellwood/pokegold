from __future__ import annotations

import argparse
import json
from pathlib import Path

from .app import run_server
from .data import (
    ALLOWED_PAIRWISE_CHOICES,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    DEFAULT_REPORT_PATH,
    PreferenceDataError,
    append_label,
    load_fixtures,
    load_labels,
    load_preferences,
    save_preference,
    write_report,
)
from .threat_availability import (
    DEFAULT_THREAT_JSON_PATH,
    DEFAULT_THREAT_REPORT_PATH,
    write_threat_report,
)


def path_arg(value: str) -> Path:
    return Path(value)


def add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    parser.add_argument("--labels", type=path_arg, default=DEFAULT_LABELS_PATH)
    parser.add_argument("--preferences", type=path_arg, default=DEFAULT_PREFERENCES_PATH)


def cmd_validate(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.fixtures)
    labels = load_labels(args.labels, fixtures=fixtures)
    preferences = load_preferences(args.preferences, fixtures=fixtures)
    print(f"Preference fixtures valid: {len(fixtures)}")
    print(f"Preference labels valid: {len(labels)}")
    print(f"Pairwise preferences valid: {len(preferences)}")
    return 0


def cmd_label(args: argparse.Namespace) -> int:
    record = append_label(
        fixture_id=args.fixture_id,
        action_id=args.action_id,
        label=args.label,
        rank=args.rank,
        note=args.note,
        fixtures_path=args.fixtures,
        labels_path=args.labels,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def cmd_prefer(args: argparse.Namespace) -> int:
    reason_tags = [tag for tag in args.reason_tags.split(",") if tag]
    action_tags = {}
    for item in args.action_tag:
        action_id, separator, tag = item.partition(":")
        if not separator:
            raise PreferenceDataError("--action-tag must use action_id:tag")
        action_tags.setdefault(action_id, []).append(tag)
    record = save_preference(
        fixture_id=args.fixture_id,
        action_a_id=args.action_a_id,
        action_b_id=args.action_b_id,
        choice=args.choice,
        preferred_action_id=args.preferred_action_id,
        reason_tags=reason_tags,
        action_tags=action_tags,
        note=args.note,
        fixtures_path=args.fixtures,
        preferences_path=args.preferences,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    json_out = None if args.json_out == "" else args.json_out
    report = write_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        out_path=args.out,
        json_out_path=json_out,
    )
    if str(args.out) != "-":
        print(f"Wrote {args.out}")
    if json_out is not None:
        print(f"Wrote {json_out}")
    print(
        "Report summary: "
        f"{report['label_count']} labels across "
        f"{report['labeled_fixture_count']} / {report['fixture_count']} fixtures, "
        f"{report['preference_count']} pairwise preferences"
    )
    return 0


def cmd_threat_report(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.fixtures)
    report = write_threat_report(
        fixtures,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    print(
        "Threat report summary: "
        f"{len(report['checkpoints'])} checkpoints, "
        f"{len(report['fixture_threats'])} fixture threat samples"
    )
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    run_server(
        host=args.host,
        port=args.port,
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.boss_ai_preference")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    add_common_paths(validate)
    validate.set_defaults(func=cmd_validate)

    label = subparsers.add_parser("label")
    add_common_paths(label)
    label.add_argument("--fixture-id", required=True)
    label.add_argument("--action-id", required=True)
    label.add_argument("--label", required=True)
    label.add_argument("--rank", type=int)
    label.add_argument("--note", default="")
    label.set_defaults(func=cmd_label)

    prefer = subparsers.add_parser("prefer")
    add_common_paths(prefer)
    prefer.add_argument("--fixture-id", required=True)
    prefer.add_argument("--action-a-id", required=True)
    prefer.add_argument("--action-b-id", required=True)
    prefer.add_argument("--choice", choices=ALLOWED_PAIRWISE_CHOICES, required=True)
    prefer.add_argument("--preferred-action-id")
    prefer.add_argument("--reason-tags", default="")
    prefer.add_argument("--action-tag", action="append", default=[])
    prefer.add_argument("--note", default="")
    prefer.set_defaults(func=cmd_prefer)

    report = subparsers.add_parser("report")
    add_common_paths(report)
    report.add_argument("--out", type=path_arg, default=DEFAULT_REPORT_PATH)
    report.add_argument("--json-out", type=path_arg, default=DEFAULT_JSON_REPORT_PATH)
    report.set_defaults(func=cmd_report)

    threat_report = subparsers.add_parser("threat-report")
    add_common_paths(threat_report)
    threat_report.add_argument("--out", type=path_arg, default=DEFAULT_THREAT_REPORT_PATH)
    threat_report.add_argument("--json-out", type=path_arg, default=DEFAULT_THREAT_JSON_PATH)
    threat_report.set_defaults(func=cmd_threat_report)

    serve = subparsers.add_parser("serve")
    add_common_paths(serve)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PreferenceDataError as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
