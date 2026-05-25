from __future__ import annotations

import argparse
from pathlib import Path

from .active_queue import (
    DEFAULT_ACTIVE_QUEUE_JSON_PATH,
    DEFAULT_ACTIVE_QUEUE_PATH,
    DEFAULT_TRACE_DIR
)
from .benchmark_positions import (
    DEFAULT_BENCHMARK_ORACLES_PATH,
    DEFAULT_BENCHMARK_JSON_PATH,
    DEFAULT_BENCHMARK_MUTATION_JSON_PATH,
    DEFAULT_BENCHMARK_MUTATION_REPORT_PATH,
    DEFAULT_BENCHMARK_POLICY_ANSWERS_PATH,
    DEFAULT_BENCHMARK_REPORT_PATH,
    DEFAULT_BENCHMARKS_PATH
)
from .benchmark_harvest import (
    DEFAULT_BENCHMARK_HARVEST_JSON_PATH,
    DEFAULT_BENCHMARK_HARVEST_REPORT_PATH,
    DEFAULT_BENCHMARK_LABEL_QUEUE_JSON_PATH,
    DEFAULT_BENCHMARK_LABEL_QUEUE_REPORT_PATH
)

from .counterfactuals import (
    DEFAULT_COUNTERFACTUAL_JSON_PATH,
    DEFAULT_COUNTERFACTUAL_REPORT_PATH
)
from .data import (
    ALLOWED_CONFIDENCE,
    ALLOWED_LESSON_TYPES,
    ALLOWED_PAIRWISE_CHOICES,
    ALLOWED_PUBLIC_INFO_SCOPES,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    DEFAULT_REPORT_PATH
)
from .features import (
    DEFAULT_FEATURE_JSON_PATH,
    DEFAULT_FEATURE_REPORT_PATH
)
from .expert_play_research import (
    DEFAULT_EXPERT_PLAY_RESEARCH_JSON_PATH,
    DEFAULT_EXPERT_PLAY_RESEARCH_REPORT_PATH
)
from .final_report import (
    DEFAULT_FINAL_JSON_PATH,
    DEFAULT_FINAL_REPORT_PATH
)
from .lessons import (
    DEFAULT_LESSON_JSON_PATH,
    DEFAULT_LESSON_REPORT_PATH,
    DEFAULT_LESSONS_PATH
)
from .long_battle_review import (
    DEFAULT_LONG_BATTLE_REVIEW_JSON_PATH,
    DEFAULT_LONG_BATTLE_REVIEW_REPORT_PATH
)
from .plan_queue import (
    DEFAULT_COACH_JSON_PATH,
    DEFAULT_COACH_REPORT_PATH,
    DEFAULT_PLAN_QUEUE_JSON_PATH,
    DEFAULT_PLAN_QUEUE_PATH
)
from .reward_model import (
    DEFAULT_REWARD_MODEL_JSON_PATH,
    DEFAULT_REWARD_MODEL_REPORT_PATH
)
from .proposals import (
    DEFAULT_PROPOSAL_JSON_PATH,
    DEFAULT_PROPOSAL_REPORT_PATH
)
from .threat_availability import (
    DEFAULT_THREAT_JSON_PATH,
    DEFAULT_THREAT_REPORT_PATH
)
from .type_evidence import (
    DEFAULT_TYPE_EVIDENCE_JSON_PATH,
    DEFAULT_TYPE_EVIDENCE_REPORT_PATH
)
from .trajectory_data import (
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_JSON_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    DEFAULT_TRAJECTORY_REPORT_PATH
)
from .commands import (
    cmd_active_queue,
    cmd_benchmark_harvest,
    cmd_benchmark_label_queue,
    cmd_benchmark_mutations,
    cmd_benchmark_policy,
    cmd_benchmark_report,
    cmd_coach_report,
    cmd_expert_play_research,
    cmd_feature_report,
    cmd_final_report,
    cmd_fit_model,
    cmd_generate_counterfactuals,
    cmd_label,
    cmd_lesson_report,
    cmd_long_battle_review,
    cmd_plan_queue,
    cmd_prefer,
    cmd_propose,
    cmd_report,
    cmd_serve,
    cmd_threat_report,
    cmd_trajectory_report,
    cmd_type_evidence,
    cmd_validate
)


def path_arg(value: str) -> Path:
    return Path(value)


def add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    parser.add_argument("--labels", type=path_arg, default=DEFAULT_LABELS_PATH)
    parser.add_argument("--preferences", type=path_arg, default=DEFAULT_PREFERENCES_PATH)


def add_trajectory_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--trajectories", type=path_arg, default=DEFAULT_TRAJECTORY_PREFERENCES_PATH)
    parser.add_argument("--demonstrations", type=path_arg, default=DEFAULT_PLAN_DEMONSTRATIONS_PATH)


def add_include_trajectories_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--include-trajectories",
        action="store_true",
        default=True,
        help="Include Coach Mode trajectory rows. This is the default.",
    )
    parser.add_argument(
        "--no-include-trajectories",
        dest="include_trajectories",
        action="store_false",
        help="Ignore Coach Mode trajectory rows for a legacy action-only report.",
    )


def add_v2_metadata_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--confidence", choices=ALLOWED_CONFIDENCE)
    parser.add_argument("--public-info-scope", choices=ALLOWED_PUBLIC_INFO_SCOPES)
    parser.add_argument("--lesson-type", choices=ALLOWED_LESSON_TYPES)
    parser.add_argument("--condition-tag", action="append", default=[])
    parser.add_argument("--counterfactual-group")
    parser.add_argument("--holdout", action="store_true", default=None)
    parser.add_argument("--source-team-hash")
    parser.add_argument("--stale-reason")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.boss_ai_preference")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    add_common_paths(validate)
    add_trajectory_paths(validate)
    validate.add_argument("--benchmarks", type=path_arg, default=DEFAULT_BENCHMARKS_PATH)
    validate.add_argument("--oracles", type=path_arg, default=DEFAULT_BENCHMARK_ORACLES_PATH)
    validate.set_defaults(func=cmd_validate)

    benchmark_report = subparsers.add_parser("benchmark-report")
    benchmark_report.add_argument(
        "--benchmarks",
        type=path_arg,
        default=DEFAULT_BENCHMARKS_PATH,
    )
    benchmark_report.add_argument(
        "--oracles",
        type=path_arg,
        default=DEFAULT_BENCHMARK_ORACLES_PATH,
    )
    benchmark_report.add_argument("--answers", type=path_arg)
    benchmark_report.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_REPORT_PATH,
    )
    benchmark_report.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_JSON_PATH,
    )
    benchmark_report.set_defaults(func=cmd_benchmark_report)

    benchmark_policy = subparsers.add_parser("benchmark-policy")
    benchmark_policy.add_argument(
        "--benchmarks",
        type=path_arg,
        default=DEFAULT_BENCHMARKS_PATH,
    )
    benchmark_policy.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_POLICY_ANSWERS_PATH,
    )
    benchmark_policy.set_defaults(func=cmd_benchmark_policy)

    benchmark_mutations = subparsers.add_parser("benchmark-mutations")
    benchmark_mutations.add_argument(
        "--benchmarks",
        type=path_arg,
        default=DEFAULT_BENCHMARKS_PATH,
    )
    benchmark_mutations.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_MUTATION_REPORT_PATH,
    )
    benchmark_mutations.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_MUTATION_JSON_PATH,
    )
    benchmark_mutations.set_defaults(func=cmd_benchmark_mutations)

    benchmark_harvest = subparsers.add_parser("benchmark-harvest")
    benchmark_harvest.add_argument(
        "--fixtures",
        type=path_arg,
        default=DEFAULT_FIXTURES_PATH,
    )
    benchmark_harvest.add_argument(
        "--preferences",
        type=path_arg,
        default=DEFAULT_PREFERENCES_PATH,
    )
    benchmark_harvest.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_HARVEST_REPORT_PATH,
    )
    benchmark_harvest.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_HARVEST_JSON_PATH,
    )
    benchmark_harvest.set_defaults(func=cmd_benchmark_harvest)

    benchmark_label_queue = subparsers.add_parser("benchmark-label-queue")
    benchmark_label_queue.add_argument(
        "--fixtures",
        type=path_arg,
        default=DEFAULT_FIXTURES_PATH,
    )
    benchmark_label_queue.add_argument(
        "--preferences",
        type=path_arg,
        default=DEFAULT_PREFERENCES_PATH,
    )
    benchmark_label_queue.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_LABEL_QUEUE_REPORT_PATH,
    )
    benchmark_label_queue.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_BENCHMARK_LABEL_QUEUE_JSON_PATH,
    )
    benchmark_label_queue.add_argument("--limit", type=int, default=20)
    benchmark_label_queue.set_defaults(func=cmd_benchmark_label_queue)

    type_evidence = subparsers.add_parser("type-evidence")
    type_evidence.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_TYPE_EVIDENCE_REPORT_PATH,
    )
    type_evidence.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_TYPE_EVIDENCE_JSON_PATH,
    )
    type_evidence.set_defaults(func=cmd_type_evidence)

    long_battle_review = subparsers.add_parser("long-battle-review")
    long_battle_review.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_LONG_BATTLE_REVIEW_REPORT_PATH,
    )
    long_battle_review.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_LONG_BATTLE_REVIEW_JSON_PATH,
    )
    long_battle_review.set_defaults(func=cmd_long_battle_review)

    expert_play_research = subparsers.add_parser("expert-play-research")
    expert_play_research.add_argument(
        "--out",
        type=path_arg,
        default=DEFAULT_EXPERT_PLAY_RESEARCH_REPORT_PATH,
    )
    expert_play_research.add_argument(
        "--json-out",
        type=path_arg,
        default=DEFAULT_EXPERT_PLAY_RESEARCH_JSON_PATH,
    )
    expert_play_research.set_defaults(func=cmd_expert_play_research)

    label = subparsers.add_parser("label")
    add_common_paths(label)
    label.add_argument("--fixture-id", required=True)
    label.add_argument("--action-id", required=True)
    label.add_argument("--label", required=True)
    label.add_argument("--rank", type=int)
    label.add_argument("--note", default="")
    add_v2_metadata_args(label)
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
    add_v2_metadata_args(prefer)
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

    feature_report = subparsers.add_parser("feature-report")
    feature_report.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    feature_report.add_argument("--out", type=path_arg, default=DEFAULT_FEATURE_REPORT_PATH)
    feature_report.add_argument("--json-out", type=path_arg, default=DEFAULT_FEATURE_JSON_PATH)
    feature_report.set_defaults(func=cmd_feature_report)

    active_queue = subparsers.add_parser("active-queue")
    add_common_paths(active_queue)
    active_queue.add_argument("--out", type=path_arg, default=DEFAULT_ACTIVE_QUEUE_PATH)
    active_queue.add_argument("--json-out", type=path_arg, default=DEFAULT_ACTIVE_QUEUE_JSON_PATH)
    active_queue.add_argument("--trace-dir", type=path_arg, default=DEFAULT_TRACE_DIR)
    active_queue.add_argument("--limit", type=int, default=20)
    active_queue.set_defaults(func=cmd_active_queue)

    plan_queue = subparsers.add_parser("plan-queue")
    add_common_paths(plan_queue)
    add_trajectory_paths(plan_queue)
    plan_queue.add_argument("--out", type=path_arg, default=DEFAULT_PLAN_QUEUE_PATH)
    plan_queue.add_argument("--json-out", type=path_arg, default=DEFAULT_PLAN_QUEUE_JSON_PATH)
    plan_queue.add_argument("--trace-dir", type=path_arg, default=DEFAULT_TRACE_DIR)
    plan_queue.add_argument("--limit", type=int, default=20)
    plan_queue.add_argument("--rollout-mode", default="deterministic_public_worst_case")
    plan_queue.set_defaults(func=cmd_plan_queue)

    counterfactuals = subparsers.add_parser("generate-counterfactuals")
    add_common_paths(counterfactuals)
    counterfactuals.add_argument("--out", type=path_arg, default=DEFAULT_COUNTERFACTUAL_REPORT_PATH)
    counterfactuals.add_argument("--json-out", type=path_arg, default=DEFAULT_COUNTERFACTUAL_JSON_PATH)
    counterfactuals.add_argument("--dry-run", action="store_true", default=True)
    counterfactuals.add_argument("--limit", type=int, default=60)
    counterfactuals.set_defaults(func=cmd_generate_counterfactuals)

    lesson_report = subparsers.add_parser("lesson-report")
    add_common_paths(lesson_report)
    add_trajectory_paths(lesson_report)
    lesson_report.add_argument("--lessons", type=path_arg, default=DEFAULT_LESSONS_PATH)
    lesson_report.add_argument("--out", type=path_arg, default=DEFAULT_LESSON_REPORT_PATH)
    lesson_report.add_argument("--json-out", type=path_arg, default=DEFAULT_LESSON_JSON_PATH)
    add_include_trajectories_arg(lesson_report)
    lesson_report.set_defaults(func=cmd_lesson_report)

    trajectory_report = subparsers.add_parser("trajectory-report")
    trajectory_report.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    add_trajectory_paths(trajectory_report)
    trajectory_report.add_argument("--out", type=path_arg, default=DEFAULT_TRAJECTORY_REPORT_PATH)
    trajectory_report.add_argument("--json-out", type=path_arg, default=DEFAULT_TRAJECTORY_JSON_PATH)
    trajectory_report.set_defaults(func=cmd_trajectory_report)

    fit_model = subparsers.add_parser("fit-model")
    fit_model.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    fit_model.add_argument("--preferences", type=path_arg, default=DEFAULT_PREFERENCES_PATH)
    fit_model.add_argument("--trajectories", type=path_arg, default=DEFAULT_TRAJECTORY_PREFERENCES_PATH)
    fit_model.add_argument("--out", type=path_arg, default=DEFAULT_REWARD_MODEL_REPORT_PATH)
    fit_model.add_argument("--json-out", type=path_arg, default=DEFAULT_REWARD_MODEL_JSON_PATH)
    fit_model.add_argument("--epochs", type=int, default=500)
    fit_model.add_argument("--learning-rate", type=float, default=0.08)
    fit_model.add_argument("--l2", type=float, default=0.02)
    add_include_trajectories_arg(fit_model)
    fit_model.set_defaults(func=cmd_fit_model)

    propose = subparsers.add_parser("propose")
    add_common_paths(propose)
    add_trajectory_paths(propose)
    propose.add_argument("--lessons", type=path_arg, default=DEFAULT_LESSONS_PATH)
    propose.add_argument("--out", type=path_arg, default=DEFAULT_PROPOSAL_REPORT_PATH)
    propose.add_argument("--json-out", type=path_arg, default=DEFAULT_PROPOSAL_JSON_PATH)
    add_include_trajectories_arg(propose)
    propose.set_defaults(func=cmd_propose)

    coach_report = subparsers.add_parser("coach-report")
    add_common_paths(coach_report)
    add_trajectory_paths(coach_report)
    coach_report.add_argument("--out", type=path_arg, default=DEFAULT_COACH_REPORT_PATH)
    coach_report.add_argument("--json-out", type=path_arg, default=DEFAULT_COACH_JSON_PATH)
    coach_report.add_argument("--trace-dir", type=path_arg, default=DEFAULT_TRACE_DIR)
    coach_report.add_argument("--limit", type=int, default=20)
    coach_report.add_argument("--rollout-mode", default="deterministic_public_worst_case")
    coach_report.set_defaults(func=cmd_coach_report)

    final_report = subparsers.add_parser("final-report")
    add_common_paths(final_report)
    add_trajectory_paths(final_report)
    final_report.add_argument("--lessons", type=path_arg, default=DEFAULT_LESSONS_PATH)
    final_report.add_argument("--out", type=path_arg, default=DEFAULT_FINAL_REPORT_PATH)
    final_report.add_argument("--json-out", type=path_arg, default=DEFAULT_FINAL_JSON_PATH)
    final_report.set_defaults(func=cmd_final_report)

    serve = subparsers.add_parser("serve")
    add_common_paths(serve)
    add_trajectory_paths(serve)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=cmd_serve)
    return parser
