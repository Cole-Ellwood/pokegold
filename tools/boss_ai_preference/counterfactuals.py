from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    PreferenceDataError,
    load_fixtures,
    load_labels,
    load_preferences,
    validate_fixture_data,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COUNTERFACTUAL_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "counterfactuals.md"
)
DEFAULT_COUNTERFACTUAL_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "counterfactuals.json"
)


def append_public_note(fixture: dict[str, Any], note: str) -> None:
    state = fixture.setdefault("state", {})
    notes = state.setdefault("public_notes", [])
    if isinstance(notes, list):
        notes.append(note)


def player_active(fixture: dict[str, Any]) -> dict[str, Any]:
    return fixture.setdefault("state", {}).setdefault("player", {}).setdefault("active", {})


def player_priors(fixture: dict[str, Any]) -> list[str]:
    active = player_active(fixture)
    priors = active.setdefault("public_priors", [])
    if not isinstance(priors, list):
        priors = []
        active["public_priors"] = priors
    return priors


def make_variant(
    fixture: dict[str, Any],
    *,
    template: str,
    suffix: str,
    rationale: str,
    changed_fields: dict[str, Any],
) -> dict[str, Any]:
    variant = copy.deepcopy(fixture)
    variant["id"] = f"{fixture['id']}__cf_{suffix}"
    variant["generated"] = True
    variant["parent_fixture_id"] = fixture["id"]
    variant["mutation_template"] = template
    variant["changed_fields"] = changed_fields
    variant["rationale"] = rationale
    variant["counterfactual_group"] = f"{fixture['id']}__{template}"
    return variant


def hp_threshold_variants(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for hp, suffix, rationale in (
        ("18%", "hp_ko_range", "Tests whether immediate KO pressure should dominate setup or status."),
        ("54%", "hp_2hko_range", "Tests the boundary where chip may set up a teammate but not end the turn."),
        ("88%", "hp_comfortable", "Tests whether slow plans are acceptable when the target is healthy."),
    ):
        variant = make_variant(
            fixture,
            template="hp_threshold",
            suffix=suffix,
            rationale=rationale,
            changed_fields={"state.player.active.hp": hp},
        )
        player_active(variant)["hp"] = hp
        append_public_note(variant, f"Counterfactual HP threshold: player active HP is {hp}.")
        variants.append(variant)
    return variants


def speed_boundary_variants(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for relation, suffix in (
        ("boss is publicly observed faster", "boss_faster"),
        ("player is publicly observed faster", "player_faster"),
        ("turn order is not yet observed", "speed_unknown"),
    ):
        variant = make_variant(
            fixture,
            template="speed_boundary",
            suffix=suffix,
            rationale="Tests setup and revenge-kill judgments around known turn order.",
            changed_fields={"state.public_notes": relation},
        )
        append_public_note(variant, f"Counterfactual speed boundary: {relation}.")
        variants.append(variant)
    return variants


def status_aftermath_variants(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for status, suffix, note in (
        ("paralyzed", "target_paralyzed", "status setup is already established"),
        ("asleep", "target_asleep", "sleep pressure already landed"),
        ("none", "sleep_clause_occupied", "another visible player party member is already asleep"),
    ):
        variant = make_variant(
            fixture,
            template="status_aftermath",
            suffix=suffix,
            rationale="Tests whether status moves are legal, useful, or redundant after public status changes.",
            changed_fields={"state.player.active.status": status},
        )
        player_active(variant)["status"] = status
        if suffix == "sleep_clause_occupied":
            variant.setdefault("state", {}).setdefault("field", {})["sleep_clause"] = "player_already_has_sleep"
        append_public_note(variant, f"Counterfactual status aftermath: {note}.")
        variants.append(variant)
    return variants


def hidden_coverage_variants(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for prior, suffix, rationale in (
        (
            "hidden coverage plausible from public learnset",
            "coverage_plausible",
            "Tests whether scouting beats greedy setup when a coverage threat is plausible.",
        ),
        (
            "coverage threat revealed",
            "coverage_revealed",
            "Tests hard respect for a now-public coverage threat.",
        ),
        (
            "coverage blocked by four revealed non-coverage moves",
            "coverage_blocked",
            "Tests that the AI stops respecting impossible hidden coverage.",
        ),
    ):
        variant = make_variant(
            fixture,
            template="hidden_coverage",
            suffix=suffix,
            rationale=rationale,
            changed_fields={"state.player.active.public_priors": prior},
        )
        player_priors(variant).append(prior)
        append_public_note(variant, f"Counterfactual hidden coverage: {prior}.")
        variants.append(variant)
    return variants


def switch_fit_variants(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for fit, suffix in (
        ("safe switch-in absorbs the public hit", "safe_switch"),
        ("risky switch-in takes meaningful chip", "risky_switch"),
        ("bad switch-in loses to the same public threat", "bad_switch"),
    ):
        variant = make_variant(
            fixture,
            template="switch_fit",
            suffix=suffix,
            rationale="Tests when an other_better/switch lesson should override move scoring.",
            changed_fields={"state.public_notes": fit},
        )
        append_public_note(variant, f"Counterfactual switch fit: {fit}.")
        variants.append(variant)
    return variants


def selected_templates(
    fixture: dict[str, Any],
    preferences: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> list[str]:
    tags = set(fixture.get("tags", []))
    fixture_preferences = [
        preference for preference in preferences if preference["fixture_id"] == fixture["id"]
    ]
    fixture_labels = [label for label in labels if label["fixture_id"] == fixture["id"]]
    note_text = " ".join(
        str(record.get("note", ""))
        for record in [*fixture_preferences, *fixture_labels]
    ).lower()
    templates: list[str] = []

    if {"setup", "setup_lock", "tempo"} & tags or "setup" in note_text:
        templates.extend(["speed_boundary", "hp_threshold"])
    if {"sleep", "status"} & tags or "sleep" in note_text:
        templates.append("status_aftermath")
    if "hidden_coverage" in tags or "hidden" in note_text or "ice" in note_text:
        templates.append("hidden_coverage")
    if any(preference["choice"] == "other_better" for preference in fixture_preferences):
        templates.append("switch_fit")
    if "switch" in note_text or "preserve" in note_text or "save" in note_text:
        templates.append("switch_fit")
    if not templates and (fixture_preferences or fixture_labels):
        templates.append("hp_threshold")

    return sorted(set(templates))


def generate_counterfactuals(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    *,
    limit: int = 60,
) -> list[dict[str, Any]]:
    generators = {
        "hidden_coverage": hidden_coverage_variants,
        "hp_threshold": hp_threshold_variants,
        "speed_boundary": speed_boundary_variants,
        "status_aftermath": status_aftermath_variants,
        "switch_fit": switch_fit_variants,
    }
    generated: list[dict[str, Any]] = []
    for fixture in fixtures:
        for template in selected_templates(fixture, preferences, labels):
            generated.extend(generators[template](fixture))
            if len(generated) >= limit:
                return generated[:limit]
    return generated[:limit]


def build_counterfactual_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    *,
    limit: int = 60,
    dry_run: bool = True,
) -> dict[str, Any]:
    generated = generate_counterfactuals(fixtures, labels, preferences, limit=limit)
    validation_errors = validate_fixture_data({"schema_version": 1, "fixtures": generated})
    if validation_errors:
        raise PreferenceDataError("\n".join(validation_errors))
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "dry_run": dry_run,
        "source_fixture_count": len(fixtures),
        "generated_count": len(generated),
        "generated_fixtures": generated,
    }


def render_counterfactual_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Counterfactual Fixture Families",
        "",
        f"Generated: {report['generated_at']}",
        f"Dry run: {str(report['dry_run']).lower()}",
        "",
        f"Generated {report['generated_count']} fixture variant(s).",
        "",
    ]
    for fixture in report["generated_fixtures"]:
        lines.extend(
            [
                f"## {fixture['id']}",
                "",
                f"- Parent: `{fixture['parent_fixture_id']}`",
                f"- Template: `{fixture['mutation_template']}`",
                f"- Group: `{fixture['counterfactual_group']}`",
                f"- Rationale: {fixture['rationale']}",
                f"- Changed fields: `{json.dumps(fixture['changed_fields'], sort_keys=True)}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_counterfactual_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    out_path: Path = DEFAULT_COUNTERFACTUAL_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_COUNTERFACTUAL_JSON_PATH,
    dry_run: bool = True,
    limit: int = 60,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    report = build_counterfactual_report(
        fixtures,
        labels,
        preferences,
        limit=limit,
        dry_run=dry_run,
    )
    markdown = render_counterfactual_report(report)

    if str(out_path) == "-":
        print(markdown)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8", newline="\n")

    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
