from __future__ import annotations

import argparse
import json

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


def metric_label(metrics: dict[str, object]) -> str:
    label = metrics.get("accuracy_label")
    if isinstance(label, str):
        return label
    accuracy = metrics.get("accuracy")
    return f"{float(accuracy):.1%}" if accuracy is not None else "n/a"


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
