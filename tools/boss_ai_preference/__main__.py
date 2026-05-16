from __future__ import annotations

import argparse
import json
from pathlib import Path

from .active_queue import (
    DEFAULT_ACTIVE_QUEUE_JSON_PATH,
    DEFAULT_ACTIVE_QUEUE_PATH,
    DEFAULT_TRACE_DIR,
    write_active_queue,
)
from .benchmark_positions import (
    DEFAULT_BENCHMARK_ORACLES_PATH,
    DEFAULT_BENCHMARK_JSON_PATH,
    DEFAULT_BENCHMARK_MUTATION_JSON_PATH,
    DEFAULT_BENCHMARK_MUTATION_REPORT_PATH,
    DEFAULT_BENCHMARK_POLICY_ANSWERS_PATH,
    DEFAULT_BENCHMARK_REPORT_PATH,
    DEFAULT_BENCHMARKS_PATH,
    load_benchmark_oracles,
    load_benchmarks,
    write_benchmark_mutation_report,
    write_benchmark_policy_answers,
    write_benchmark_report,
)
from .benchmark_harvest import (
    DEFAULT_BENCHMARK_HARVEST_JSON_PATH,
    DEFAULT_BENCHMARK_HARVEST_REPORT_PATH,
    DEFAULT_BENCHMARK_LABEL_QUEUE_JSON_PATH,
    DEFAULT_BENCHMARK_LABEL_QUEUE_REPORT_PATH,
    write_benchmark_harvest_report,
    write_benchmark_label_queue,
)
from .app import run_server
from .counterfactuals import (
    DEFAULT_COUNTERFACTUAL_JSON_PATH,
    DEFAULT_COUNTERFACTUAL_REPORT_PATH,
    write_counterfactual_report,
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
    DEFAULT_REPORT_PATH,
    PreferenceDataError,
    append_label,
    load_fixtures,
    load_labels,
    load_preferences,
    save_preference,
    write_report,
)
from .features import (
    DEFAULT_FEATURE_JSON_PATH,
    DEFAULT_FEATURE_REPORT_PATH,
    write_feature_report,
)
from .expert_play_research import (
    DEFAULT_EXPERT_PLAY_RESEARCH_JSON_PATH,
    DEFAULT_EXPERT_PLAY_RESEARCH_REPORT_PATH,
    write_expert_play_research_report,
)
from .final_report import (
    DEFAULT_FINAL_JSON_PATH,
    DEFAULT_FINAL_REPORT_PATH,
    write_final_report,
)
from .lessons import (
    DEFAULT_LESSON_JSON_PATH,
    DEFAULT_LESSON_REPORT_PATH,
    DEFAULT_LESSONS_PATH,
    write_lesson_report,
)
from .long_battle_review import (
    DEFAULT_LONG_BATTLE_REVIEW_JSON_PATH,
    DEFAULT_LONG_BATTLE_REVIEW_REPORT_PATH,
    write_long_battle_review_report,
)
from .plan_queue import (
    DEFAULT_COACH_JSON_PATH,
    DEFAULT_COACH_REPORT_PATH,
    DEFAULT_PLAN_QUEUE_JSON_PATH,
    DEFAULT_PLAN_QUEUE_PATH,
    write_coach_report,
    write_plan_queue,
)
from .reward_model import (
    DEFAULT_REWARD_MODEL_JSON_PATH,
    DEFAULT_REWARD_MODEL_REPORT_PATH,
    write_reward_model_report,
)
from .proposals import (
    DEFAULT_PROPOSAL_JSON_PATH,
    DEFAULT_PROPOSAL_REPORT_PATH,
    write_proposal_report,
)
from .threat_availability import (
    DEFAULT_THREAT_JSON_PATH,
    DEFAULT_THREAT_REPORT_PATH,
    write_threat_report,
)
from .type_evidence import (
    DEFAULT_TYPE_EVIDENCE_JSON_PATH,
    DEFAULT_TYPE_EVIDENCE_REPORT_PATH,
    write_type_evidence_report,
)
from .trajectory_data import (
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_JSON_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    DEFAULT_TRAJECTORY_REPORT_PATH,
    load_plan_demonstrations,
    load_trajectory_preferences,
    write_trajectory_report,
)
from .trajectory_regression import (
    evaluate_trajectory_corpus,
    format_result as format_trajectory_regression,
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


def metric_label(metrics: dict[str, object]) -> str:
    label = metrics.get("accuracy_label")
    if isinstance(label, str):
        return label
    accuracy = metrics.get("accuracy")
    return f"{float(accuracy):.1%}" if accuracy is not None else "n/a"


def add_v2_metadata_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--confidence", choices=ALLOWED_CONFIDENCE)
    parser.add_argument("--public-info-scope", choices=ALLOWED_PUBLIC_INFO_SCOPES)
    parser.add_argument("--lesson-type", choices=ALLOWED_LESSON_TYPES)
    parser.add_argument("--condition-tag", action="append", default=[])
    parser.add_argument("--counterfactual-group")
    parser.add_argument("--holdout", action="store_true", default=None)
    parser.add_argument("--source-team-hash")
    parser.add_argument("--stale-reason")


def v2_metadata_kwargs(args: argparse.Namespace) -> dict[str, object]:
    return {
        "confidence": args.confidence,
        "public_info_scope": args.public_info_scope,
        "lesson_type": args.lesson_type,
        "condition_tags": args.condition_tag,
        "counterfactual_group": args.counterfactual_group,
        "holdout": args.holdout,
        "source_team_hash": args.source_team_hash,
        "stale_reason": args.stale_reason,
    }


def cmd_validate(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.fixtures)
    labels = load_labels(args.labels, fixtures=fixtures)
    preferences = load_preferences(args.preferences, fixtures=fixtures)
    trajectories = load_trajectory_preferences(args.trajectories, fixtures=fixtures)
    demonstrations = load_plan_demonstrations(args.demonstrations, fixtures=fixtures)
    benchmarks = load_benchmarks(args.benchmarks)
    oracles = load_benchmark_oracles(args.oracles)
    print(f"Preference fixtures valid: {len(fixtures)}")
    print(f"Preference labels valid: {len(labels)}")
    print(f"Pairwise preferences valid: {len(preferences)}")
    print(f"Trajectory preferences valid: {len(trajectories)}")
    print(f"Plan demonstrations valid: {len(demonstrations)}")
    print(f"State-transition public cards valid: {len(benchmarks)}")
    print(f"State-transition hidden oracles valid: {len(oracles)}")
    return 0


def cmd_benchmark_report(args: argparse.Namespace) -> int:
    report = write_benchmark_report(
        benchmarks_path=args.benchmarks,
        oracles_path=args.oracles,
        answers_path=args.answers,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "State-transition benchmark summary: "
        f"{report['benchmark_count']} benchmarks, "
        f"contract_ready={report['benchmark_contract_ready']}, "
        f"policy_evaluated={report['policy_evaluated']}, "
        f"policy_passes={report['policy_passes']}"
    )
    return 0


def cmd_benchmark_policy(args: argparse.Namespace) -> int:
    report = write_benchmark_policy_answers(
        benchmarks_path=args.benchmarks,
        out_path=args.out,
    )
    print(f"Wrote {args.out}")
    print(
        "State-transition policy answer summary: "
        f"{len(report['answers'])} answers from {report['policy_name']}"
    )
    return 0


def cmd_benchmark_mutations(args: argparse.Namespace) -> int:
    report = write_benchmark_mutation_report(
        benchmarks_path=args.benchmarks,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "State-transition mutation summary: "
        f"{report['mutation_count']} mutations, "
        f"policy_flips={report['policy_flip_count']}, "
        f"all_pass={report['all_mutations_pass']}"
    )
    return 0


def cmd_benchmark_harvest(args: argparse.Namespace) -> int:
    report = write_benchmark_harvest_report(
        fixtures_path=args.fixtures,
        preferences_path=args.preferences,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Fixture benchmark harvest summary: "
        f"{report['complete_candidate_count']} complete, "
        f"{report['partial_candidate_count']} partial"
    )
    return 0


def cmd_benchmark_label_queue(args: argparse.Namespace) -> int:
    report = write_benchmark_label_queue(
        fixtures_path=args.fixtures,
        preferences_path=args.preferences,
        out_path=args.out,
        json_out_path=args.json_out,
        limit=args.limit,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Benchmark label queue summary: "
        f"{report['returned_count']} / {report['request_count']} requests, "
        f"{report['one_label_completion_count']} one-label completions"
    )
    return 0


def cmd_type_evidence(args: argparse.Namespace) -> int:
    report = write_type_evidence_report(
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Type-effectiveness evidence summary: "
        f"{report['chart_tweak_count']} chart tweaks, "
        f"{report['text_claim_count']} text claims, "
        f"unsupported={report['unsupported_text_claim_count']}, "
        f"all_pass={report['all_pass']}"
    )
    return 0


def cmd_long_battle_review(args: argparse.Namespace) -> int:
    report = write_long_battle_review_report(
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Long battle review summary: "
        f"{report['turn_count']} turns, "
        f"{report['critical_turn_count']} critical turns, "
        f"valid={report['reviews_valid']}"
    )
    return 0


def cmd_expert_play_research(args: argparse.Namespace) -> int:
    report = write_expert_play_research_report(
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Expert play research summary: "
        f"{report['principle_count']} source-backed principles"
    )
    return 0


def cmd_label(args: argparse.Namespace) -> int:
    record = append_label(
        fixture_id=args.fixture_id,
        action_id=args.action_id,
        label=args.label,
        rank=args.rank,
        note=args.note,
        **v2_metadata_kwargs(args),
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
        **v2_metadata_kwargs(args),
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


def cmd_feature_report(args: argparse.Namespace) -> int:
    report = write_feature_report(
        fixtures_path=args.fixtures,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Feature report summary: "
        f"{report['action_count']} actions, "
        f"{report['feature_count']} feature names"
    )
    return 0


def cmd_active_queue(args: argparse.Namespace) -> int:
    report = write_active_queue(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        out_path=args.out,
        json_out_path=args.json_out,
        trace_dir=args.trace_dir,
        limit=args.limit,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Active queue summary: "
        f"{report['returned_count']} / {report['candidate_count']} candidates"
    )
    return 0


def cmd_plan_queue(args: argparse.Namespace) -> int:
    report = write_plan_queue(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
        out_path=args.out,
        json_out_path=args.json_out,
        trace_dir=args.trace_dir,
        limit=args.limit,
        rollout_mode=args.rollout_mode,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Plan queue summary: "
        f"{report['returned_count']} / {report['candidate_count']} candidates"
    )
    return 0


def cmd_generate_counterfactuals(args: argparse.Namespace) -> int:
    report = write_counterfactual_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        out_path=args.out,
        json_out_path=args.json_out,
        dry_run=args.dry_run,
        limit=args.limit,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Counterfactual summary: "
        f"{report['generated_count']} generated variants"
    )
    return 0


def cmd_lesson_report(args: argparse.Namespace) -> int:
    report = write_lesson_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories if args.include_trajectories else None,
        lessons_path=args.lessons,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Lesson report summary: "
        f"{report['lesson_count']} lessons, "
        f"{len(report['stale_direct_actions'])} stale direct-action rows"
    )
    return 0


def cmd_trajectory_report(args: argparse.Namespace) -> int:
    report = write_trajectory_report(
        fixtures_path=args.fixtures,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Trajectory report summary: "
        f"{report['trajectory_count']} preferences, "
        f"{report['demonstration_count']} demonstrations"
    )
    return 0


def cmd_trajectory_regress(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.fixtures)
    trajectories = load_trajectory_preferences(args.trajectories, fixtures=fixtures)
    result = evaluate_trajectory_corpus(
        fixtures,
        trajectories,
        threshold=args.threshold,
        canonical_scope=args.canonical_scope,
    )
    print(format_trajectory_regression(result))
    if args.json_out is not None:
        payload = {
            "generated_at": result.generated_at,
            "threshold": result.threshold,
            "strict_label_count": result.strict_label_count,
            "strict_agreement_count": result.strict_agreement_count,
            "agreement_rate": result.agreement_rate,
            "passed": result.passed,
            "skipped": result.skipped,
            "tie_first_moves": result.tie_first_moves,
            "cumulative_resolved": result.cumulative_resolved,
            "route_projected_resolved": result.route_projected_resolved,
            "structurally_invalid_plans_seen": result.structurally_invalid_plans_seen,
            "by_lesson_type": result.by_lesson_type,
            "disagreements": [
                {
                    "fixture_id": v.fixture_id,
                    "trajectory_a_id": v.trajectory_a_id,
                    "trajectory_b_id": v.trajectory_b_id,
                    "label_choice": v.label_choice,
                    "scorer_choice": v.scorer_choice,
                    "first_move_a": v.first_move_a,
                    "first_move_b": v.first_move_b,
                    "score_a": v.score_a,
                    "score_b": v.score_b,
                    "same_first_move": v.same_first_move,
                    "lesson_type": v.lesson_type,
                    "note": v.note,
                    "cumulative_score_a": v.cumulative_score_a,
                    "cumulative_score_b": v.cumulative_score_b,
                    "resolved_by": v.resolved_by,
                    "route_value_delta_a": v.route_value_delta_a,
                    "route_value_delta_b": v.route_value_delta_b,
                    "route_factors_a": list(v.route_factors_a),
                    "route_factors_b": list(v.route_factors_b),
                    "structurally_valid_a": v.structurally_valid_a,
                    "structurally_valid_b": v.structurally_valid_b,
                }
                for v in result.disagreements
            ],
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2))
        print(f"Wrote {args.json_out}")
    return 0 if result.passed else 1
    return 0


def cmd_fit_model(args: argparse.Namespace) -> int:
    report = write_reward_model_report(
        fixtures_path=args.fixtures,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        out_path=args.out,
        json_out_path=args.json_out,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        include_trajectories=args.include_trajectories,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Reward model summary: "
        f"{report['train_count']} train, {report['holdout_count']} holdout, "
        f"holdout accuracy {metric_label(report['holdout_metrics'])}"
    )
    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    report = write_proposal_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
        lessons_path=args.lessons,
        out_path=args.out,
        json_out_path=args.json_out,
        include_trajectories=args.include_trajectories,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(f"Proposal report summary: {report['proposal_count']} proposals")
    return 0


def cmd_coach_report(args: argparse.Namespace) -> int:
    report = write_coach_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
        out_path=args.out,
        json_out_path=args.json_out,
        trace_dir=args.trace_dir,
        limit=args.limit,
        rollout_mode=args.rollout_mode,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Coach report summary: "
        f"{report['plan_queue']['returned_count']} plan questions, "
        f"{report['trajectory_report']['trajectory_count']} trajectory preferences"
    )
    return 0


def cmd_final_report(args: argparse.Namespace) -> int:
    report = write_final_report(
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
        lessons_path=args.lessons,
        out_path=args.out,
        json_out_path=args.json_out,
    )
    print(f"Wrote {args.out}")
    if args.json_out is not None:
        print(f"Wrote {args.json_out}")
    print(
        "Final readiness summary: "
        f"ready_for_rom_scoring_review={report['ready_for_rom_scoring_review']}"
    )
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    run_server(
        host=args.host,
        port=args.port,
        fixtures_path=args.fixtures,
        labels_path=args.labels,
        preferences_path=args.preferences,
        trajectories_path=args.trajectories,
        demonstrations_path=args.demonstrations,
    )
    return 0


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

    trajectory_regress = subparsers.add_parser(
        "trajectory-regress",
        help="Grade the current Python scorer against trajectory preference labels "
             "(first-move comparison; ties on shared turn-1 actions).",
    )
    trajectory_regress.add_argument("--fixtures", type=path_arg, default=DEFAULT_FIXTURES_PATH)
    trajectory_regress.add_argument(
        "--trajectories",
        type=path_arg,
        default=DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    )
    trajectory_regress.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Minimum strict-label agreement rate (default 0.8).",
    )
    trajectory_regress.add_argument(
        "--canonical-scope",
        type=str,
        default=None,
        choices=("public_only", "public_plus_common_meta", "hidden_info_rejected", "needs_source_check"),
        help=(
            "Only grade labels whose public_info_scope matches this scope. "
            "Default: grade every strict label (legacy). Use this when the loop's "
            "canonical reasoning frame has moved (e.g. user directed Bayesian "
            "inference) so older same-fixture labels under the wrong scope don't "
            "drag down the agreement metric."
        ),
    )
    trajectory_regress.add_argument(
        "--json-out",
        type=path_arg,
        default=None,
        help="Optional path to write a JSON regression report.",
    )
    trajectory_regress.set_defaults(func=cmd_trajectory_regress)

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PreferenceDataError as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
