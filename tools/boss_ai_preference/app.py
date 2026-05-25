from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .active_queue import build_active_queue
from .boss_team import attach_boss_teams
from .damage_estimates import attach_damage_estimates
from .final_report import build_final_report, render_final_report
from .threat_availability import attach_incoming_threats
from .data import (
    ALLOWED_CONFIDENCE,
    ALLOWED_LESSON_TYPES,
    ALLOWED_REASON_TAGS,
    ALLOWED_PUBLIC_INFO_SCOPES,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    PreferenceDataError,
    append_label,
    build_report,
    load_fixtures,
    load_labels,
    load_preferences,
    render_markdown_report,
    save_preference,
)
from .plan_queue import build_coach_report, build_plan_queue, render_coach_report
from .lessons import load_lessons
from .plans import generated_plan_ids_by_fixture
from .trajectory_data import (
    ALLOWED_TRAJECTORY_CHOICES,
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    build_trajectory_report,
    load_plan_demonstrations,
    load_trajectory_preferences,
    render_trajectory_report,
    save_plan_demonstration,
    save_trajectory_preference,
)


HTML = (Path(__file__).resolve().parent / "app.html").read_text(encoding="utf-8")


def make_handler(
    fixtures_path: Path,
    labels_path: Path,
    preferences_path: Path,
    trajectories_path: Path,
    demonstrations_path: Path,
) -> type[BaseHTTPRequestHandler]:
    class PreferenceHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/":
                    self._send_html()
                elif parsed.path == "/api/fixtures":
                    fixtures = load_fixtures(fixtures_path)
                    self._send_json(
                        {
                            "fixtures": attach_boss_teams(
                                attach_incoming_threats(attach_damage_estimates(fixtures))
                            )
                        }
                    )
                elif parsed.path == "/api/labels":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    self._send_json({"labels": labels})
                elif parsed.path == "/api/preferences":
                    fixtures = load_fixtures(fixtures_path)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    self._send_json({"preferences": preferences})
                elif parsed.path == "/api/active-queue":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    self._send_json(
                        build_active_queue(fixtures, labels, preferences, limit=12)
                    )
                elif parsed.path == "/api/plan-queue":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    trajectories = load_trajectory_preferences(
                        trajectories_path,
                        fixtures=fixtures,
                    )
                    demonstrations = load_plan_demonstrations(
                        demonstrations_path,
                        fixtures=fixtures,
                    )
                    self._send_json(
                        build_plan_queue(
                            fixtures,
                            labels,
                            preferences,
                            trajectories,
                            demonstrations,
                            limit=20,
                        )
                    )
                elif parsed.path == "/api/trajectories":
                    fixtures = load_fixtures(fixtures_path)
                    trajectories = load_trajectory_preferences(
                        trajectories_path,
                        fixtures=fixtures,
                    )
                    self._send_json({"trajectories": trajectories})
                elif parsed.path == "/api/demonstrations":
                    fixtures = load_fixtures(fixtures_path)
                    demonstrations = load_plan_demonstrations(
                        demonstrations_path,
                        fixtures=fixtures,
                    )
                    self._send_json({"demonstrations": demonstrations})
                elif parsed.path == "/api/report":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    self._send_text(
                        render_markdown_report(build_report(fixtures, labels, preferences))
                    )
                elif parsed.path == "/api/trajectory-report":
                    fixtures = load_fixtures(fixtures_path)
                    trajectories = load_trajectory_preferences(
                        trajectories_path,
                        fixtures=fixtures,
                    )
                    demonstrations = load_plan_demonstrations(
                        demonstrations_path,
                        fixtures=fixtures,
                    )
                    self._send_text(
                        render_trajectory_report(
                            build_trajectory_report(fixtures, trajectories, demonstrations)
                        )
                    )
                elif parsed.path == "/api/coach-report":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    trajectories = load_trajectory_preferences(
                        trajectories_path,
                        fixtures=fixtures,
                    )
                    demonstrations = load_plan_demonstrations(
                        demonstrations_path,
                        fixtures=fixtures,
                    )
                    self._send_text(
                        render_coach_report(
                            build_coach_report(
                                fixtures,
                                labels,
                                preferences,
                                trajectories,
                                demonstrations,
                                limit=20,
                            )
                        )
                    )
                elif parsed.path == "/api/final-report":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    trajectories = load_trajectory_preferences(
                        trajectories_path,
                        fixtures=fixtures,
                    )
                    demonstrations = load_plan_demonstrations(
                        demonstrations_path,
                        fixtures=fixtures,
                    )
                    self._send_text(
                        render_final_report(
                            build_final_report(
                                fixtures,
                                labels,
                                preferences,
                                load_lessons(),
                                trajectories,
                                demonstrations,
                            )
                        )
                    )
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "not found")
            except PreferenceDataError as exc:
                self._send_text(str(exc), status=HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in {
                "/api/labels",
                "/api/preferences",
                "/api/trajectories",
                "/api/demonstrations",
            }:
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
                return
            try:
                body = self._read_json()
                if parsed.path == "/api/labels":
                    record = append_label(
                        fixture_id=body.get("fixture_id", ""),
                        action_id=body.get("action_id", ""),
                        label=body.get("label", ""),
                        rank=body.get("rank"),
                        note=body.get("note", ""),
                        confidence=body.get("confidence"),
                        public_info_scope=body.get("public_info_scope"),
                        lesson_type=body.get("lesson_type"),
                        condition_tags=body.get("condition_tags"),
                        counterfactual_group=body.get("counterfactual_group"),
                        holdout=body.get("holdout"),
                        source_team_hash=body.get("source_team_hash"),
                        stale_reason=body.get("stale_reason"),
                        fixtures_path=fixtures_path,
                        labels_path=labels_path,
                    )
                    self._send_json({"label": record}, status=HTTPStatus.CREATED)
                elif parsed.path == "/api/preferences":
                    record = save_preference(
                        fixture_id=body.get("fixture_id", ""),
                        action_a_id=body.get("action_a_id", ""),
                        action_b_id=body.get("action_b_id", ""),
                        choice=body.get("choice", ""),
                        preferred_action_id=body.get("preferred_action_id"),
                        reason_tags=body.get("reason_tags"),
                        action_tags=body.get("action_tags"),
                        note=body.get("note", ""),
                        confidence=body.get("confidence"),
                        public_info_scope=body.get("public_info_scope"),
                        lesson_type=body.get("lesson_type"),
                        condition_tags=body.get("condition_tags"),
                        counterfactual_group=body.get("counterfactual_group"),
                        holdout=body.get("holdout"),
                        source_team_hash=body.get("source_team_hash"),
                        stale_reason=body.get("stale_reason"),
                        fixtures_path=fixtures_path,
                        preferences_path=preferences_path,
                    )
                    self._send_json({"preference": record}, status=HTTPStatus.CREATED)
                elif parsed.path == "/api/trajectories":
                    fixtures = load_fixtures(fixtures_path)
                    known_plan_ids_by_fixture = generated_plan_ids_by_fixture(fixtures)
                    record = save_trajectory_preference(
                        fixture_id=body.get("fixture_id", ""),
                        trajectory_a_id=body.get("trajectory_a_id", ""),
                        trajectory_b_id=body.get("trajectory_b_id", ""),
                        choice=body.get("choice", ""),
                        preferred_trajectory_id=body.get("preferred_trajectory_id"),
                        horizon=body.get("horizon", 3),
                        confidence=body.get("confidence"),
                        public_info_scope=body.get("public_info_scope"),
                        lesson_type=body.get("lesson_type"),
                        condition_tags=body.get("condition_tags"),
                        branch_tags=body.get("branch_tags"),
                        holdout=body.get("holdout"),
                        comparison_scope=body.get("comparison_scope"),
                        compared_plan_ids=body.get("compared_plan_ids"),
                        note=body.get("note", ""),
                        fixtures_path=fixtures_path,
                        trajectories_path=trajectories_path,
                        known_plan_ids_by_fixture=known_plan_ids_by_fixture,
                    )
                    self._send_json({"trajectory": record}, status=HTTPStatus.CREATED)
                else:
                    record = save_plan_demonstration(
                        fixture_id=body.get("fixture_id", ""),
                        demonstration_id=body.get("demonstration_id", ""),
                        horizon=body.get("horizon", 3),
                        steps=body.get("steps", []),
                        near_tie_with=body.get("near_tie_with"),
                        condition_tags=body.get("condition_tags"),
                        human_summary=body.get("human_summary", ""),
                        fixtures_path=fixtures_path,
                        demonstrations_path=demonstrations_path,
                    )
                    self._send_json({"demonstration": record}, status=HTTPStatus.CREATED)
            except (PreferenceDataError, json.JSONDecodeError) as exc:
                self._send_text(str(exc), status=HTTPStatus.BAD_REQUEST)

        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise PreferenceDataError("request body must be a JSON object")
            return data

        def _send_html(self) -> None:
            html = HTML
            html = html.replace("__REASON_TAGS__", json.dumps(ALLOWED_REASON_TAGS))
            html = html.replace("__CONFIDENCE_OPTIONS__", json.dumps(ALLOWED_CONFIDENCE))
            html = html.replace("__TRAJECTORY_CHOICES__", json.dumps(ALLOWED_TRAJECTORY_CHOICES))
            html = html.replace(
                "__PUBLIC_INFO_SCOPE_OPTIONS__",
                json.dumps(ALLOWED_PUBLIC_INFO_SCOPES),
            )
            html = html.replace("__LESSON_TYPE_OPTIONS__", json.dumps(ALLOWED_LESSON_TYPES))
            encoded = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(
            self,
            payload: object,
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_text(
            self,
            text: str,
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            encoded = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return PreferenceHandler


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
) -> None:
    handler = make_handler(
        fixtures_path,
        labels_path,
        preferences_path,
        trajectories_path,
        demonstrations_path,
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Boss AI Preference Lab: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Boss AI Preference Lab.")
    finally:
        server.server_close()
