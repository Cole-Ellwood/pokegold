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


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Boss AI Preference Lab</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0b0b0f;
  --panel: #17181d;
  --panel-elevated: #202126;
  --control: #24262d;
  --control-hover: #2d3038;
  --ink: #f3f4f8;
  --muted: #a6adbb;
  --subtle: #7d8491;
  --line: #383b44;
  --line-strong: #535865;
  --selected: rgba(10, 132, 255, .18);
  --accent: #0a84ff;
  --accent-strong: #5eb0ff;
  --accent-fill: #006edb;
  --accent-fill-hover: #0a74da;
  --accent-shadow: rgba(10, 132, 255, .28);
  --good: #6ee7d8;
  --warn: #ffd18a;
}
* { box-sizing: border-box; }
html { background: var(--bg); }
body {
  margin: 0;
  font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--bg);
  overflow-x: hidden;
}
::selection {
  color: #ffffff;
  background: rgba(10, 132, 255, .55);
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 54px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: rgba(23, 24, 29, .92);
  backdrop-filter: blur(18px);
}
h1 { margin: 0; font-size: 18px; }
.top-tabs {
  display: flex;
  flex: 1;
  justify-content: center;
  gap: 6px;
}
.top-tab {
  min-width: 78px;
  padding: 7px 10px;
  font-weight: 700;
}
.top-tab.active {
  border-color: var(--accent);
  background: var(--selected);
}
h2 { margin-top: 0; }
h2, h3, label { color: var(--ink); }
main {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) minmax(280px, 360px);
  gap: 12px;
  padding: 12px;
  height: calc(100vh - 55px);
}
section {
  min-width: 0;
  overflow: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, .22);
}
.pane-title {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 10px 12px;
  font-weight: 700;
  border-bottom: 1px solid var(--line);
  background: rgba(23, 24, 29, .94);
  backdrop-filter: blur(18px);
}
.pane-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 8px;
  border-bottom: 1px solid var(--line);
}
.pane-tabs button {
  padding: 8px;
  text-align: center;
}
.pane-tabs button.active {
  border-color: var(--accent);
  background: var(--selected);
}
.fixture-list { padding: 8px; }
.hidden { display: none; }
.one-column {
  grid-template-columns: minmax(0, 1fr);
}
button {
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--control);
  color: var(--ink);
  cursor: pointer;
}
button:hover {
  border-color: var(--line-strong);
  background: var(--control-hover);
}
.fixture-button {
  display: block;
  width: 100%;
  margin: 0 0 8px;
  padding: 9px;
  text-align: left;
}
.fixture-button.active {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.fixture-button.saved:not(.active) {
  border-color: rgba(110, 231, 216, .38);
}
.fixture-button.partial:not(.active) {
  border-color: rgba(255, 209, 138, .44);
}
.fixture-button strong { display: block; font-size: 13px; }
.fixture-button span {
  overflow-wrap: anywhere;
  word-break: break-word;
  color: var(--subtle);
  font-size: 12px;
}
.queue-item .reason {
  display: block;
  margin-top: 4px;
  overflow-wrap: anywhere;
  word-break: break-word;
  color: var(--muted);
  font-size: 12px;
}
.coach-filter {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  padding: 8px;
  border-bottom: 1px solid var(--line);
}
.coach-filter button {
  padding: 7px;
  font-size: 12px;
}
.coach-filter button.active {
  border-color: var(--accent);
  background: var(--selected);
}
.plan-card {
  display: block;
  width: 100%;
  margin: 0 0 8px;
  padding: 10px;
  text-align: left;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-elevated);
}
.plan-card.selected {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.plan-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-weight: 800;
}
.plan-goal,
.plan-rationale,
.plan-stops {
  margin-top: 5px;
  color: var(--muted);
  font-size: 12px;
}
.plan-timeline {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}
.plan-turn {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 8px;
  padding: 7px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--control);
}
.plan-turn.projected {
  border-style: dashed;
  color: var(--muted);
}
.plan-turn strong {
  color: var(--accent-strong);
}
.coach-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}
.coach-actions button {
  padding: 9px;
  text-align: left;
}
.coach-actions button.selected,
.chip.selected {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.chip {
  padding: 6px 8px;
  border-radius: 999px;
  font-size: 12px;
}
.bucket-grid {
  display: grid;
  gap: 8px;
}
.bucket-row {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
}
.bucket-row strong {
  color: var(--muted);
  font-size: 12px;
}
.team-card {
  grid-column: 1 / -1;
}
.team-source {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 12px;
}
.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 8px;
}
.team-member {
  min-width: 0;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--control);
}
.team-member.active {
  border-color: var(--accent);
  background: var(--selected);
}
.team-member-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-weight: 800;
}
.team-member-facts,
.team-member-moves {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
}
.builder {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-elevated);
}
.builder-row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}
.detail { padding: 12px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.box {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  background: var(--panel-elevated);
}
.box h3 { margin: 0 0 8px; font-size: 14px; }
.active-top {
  display: grid;
  gap: 8px;
  padding-bottom: 9px;
  border-bottom: 1px solid var(--line);
}
.pokemon-name {
  font-size: 18px;
  font-weight: 800;
}
.primary-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}
.fact {
  min-width: 0;
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--control);
}
.fact span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
}
.fact strong {
  display: block;
  margin-top: 2px;
  overflow-wrap: anywhere;
  font-size: 13px;
}
.detail-list {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 6px 10px;
  margin: 9px 0 0;
}
.detail-list dt {
  color: var(--muted);
  font-weight: 700;
}
.detail-list dd {
  min-width: 0;
  margin: 0;
}
.inline-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.note-list {
  margin: 0;
  padding-left: 18px;
}
.note-list li { margin: 4px 0; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.tag {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 2px 7px;
  color: var(--muted);
  background: var(--control);
  font-size: 12px;
}
.actions { display: grid; gap: 8px; margin-top: 12px; }
.action {
  padding: 10px;
  text-align: left;
}
.action.selected {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.comparison {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}
.comparison-pair {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}
.action-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  background: var(--panel-elevated);
}
.action-card.selected {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.candidate-label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.link-button {
  width: max-content;
  padding: 7px 9px;
}
.choice-grid,
.metadata-grid,
.reason-grid {
  display: grid;
  gap: 8px;
}
.choice-grid { grid-template-columns: 1fr 1fr; }
.metadata-grid { grid-template-columns: 1fr 1fr; }
.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}
.check-row input { width: auto; }
.reason-block {
  display: grid;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-elevated);
}
.reason-title {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.choice-button,
.reason-button {
  padding: 9px;
  text-align: left;
}
.choice-button.selected,
.reason-button.selected {
  border-color: var(--accent);
  background: var(--selected);
  box-shadow: 0 0 0 2px var(--accent-shadow);
}
.action-name { font-weight: 700; }
.action-kind { color: var(--muted); font-size: 12px; }
.action p { margin: 6px 0 0; color: var(--muted); }
.damage-estimate {
  margin-top: 8px;
  padding: 7px 8px;
  border: 1px solid rgba(110, 231, 216, .35);
  border-radius: 6px;
  color: var(--ink);
  background: rgba(110, 231, 216, .08);
  font-size: 12px;
}
.damage-estimate strong { color: var(--good); }
.threat-list {
  display: grid;
  gap: 8px;
}
.threat {
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--control);
}
.threat-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.threat-name { font-weight: 800; }
.threat-bucket { color: var(--good); font-weight: 800; }
.threat-details { margin-top: 4px; color: var(--muted); font-size: 12px; }
label { display: block; margin: 10px 0 4px; font-weight: 700; }
select, input, textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px;
  font: inherit;
  color: var(--ink);
  background: var(--control);
}
select:focus, input:focus, textarea:focus, button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
textarea { min-height: 96px; resize: vertical; }
.save {
  width: 100%;
  margin-top: 12px;
  padding: 10px;
  color: #fff;
  border-color: var(--accent);
  background: var(--accent-fill);
  font-weight: 700;
}
.save:hover {
  border-color: var(--accent-strong);
  background: var(--accent-fill-hover);
}
.meta { color: var(--muted); font-size: 12px; }
.saved-summary {
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid rgba(110, 231, 216, .35);
  border-radius: 6px;
  color: var(--ink);
  background: rgba(110, 231, 216, .08);
  font-size: 12px;
}
.ok { color: var(--good); }
.warn { color: var(--warn); }
pre {
  white-space: pre-wrap;
  margin: 0;
  padding: 9px;
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--muted);
  background: var(--control);
  font-size: 12px;
}
@media (max-width: 980px) {
  main { grid-template-columns: minmax(0, 1fr); height: auto; }
  section { max-height: none; }
}
@media (max-width: 620px) {
  header {
    flex-wrap: wrap;
    align-items: stretch;
  }
  h1 {
    flex: 1 1 100%;
  }
  .top-tabs {
    order: 2;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    flex: 1 1 100%;
    width: 100%;
  }
  .top-tab {
    min-width: 0;
    padding-inline: 6px;
  }
  #summary {
    order: 3;
    width: 100%;
  }
  main {
    width: 100%;
    max-width: 100vw;
    overflow-x: hidden;
  }
  section {
    width: 100%;
    max-width: calc(100vw - 24px);
    overflow-x: hidden;
  }
  .fixture-button,
  .plan-card {
    max-width: 100%;
  }
  .coach-filter,
  .choice-grid,
  .metadata-grid,
  .coach-actions {
    grid-template-columns: 1fr;
  }
}
</style>
</head>
<body>
<header>
  <h1>Boss AI Preference Lab</h1>
  <nav class="top-tabs" aria-label="Lab sections">
    <button id="coachTopTab" class="top-tab active">Multi-Turn</button>
    <button id="queueTopTab" class="top-tab">Needs Review</button>
    <button id="reportsTopTab" class="top-tab">Reports</button>
    <button id="dataTopTab" class="top-tab">Single Turn</button>
  </nav>
  <div id="summary" class="meta"></div>
</header>
<main id="coachMain">
  <section>
    <div class="pane-title">Plan Queue</div>
    <div id="coachFilters" class="coach-filter"></div>
    <div id="coachQueue" class="fixture-list"></div>
  </section>
  <section>
    <div class="pane-title">AI Team + Public State</div>
    <div id="coachSnapshot" class="detail"></div>
  </section>
  <section>
    <div class="pane-title">3-5 Turn Answer</div>
    <div id="coachAnswer" class="detail"></div>
  </section>
</main>
<main id="reportsMain" class="hidden one-column">
  <section>
    <div class="pane-title">Reports</div>
    <div class="detail">
      <button class="link-button" id="refreshCoachReport">Refresh Reports</button>
      <h3>Final Readiness</h3>
      <pre id="finalReport"></pre>
      <h3>Coach Queue</h3>
      <pre id="coachReport"></pre>
    </div>
  </section>
</main>
<main id="dataMain" class="hidden">
  <section>
    <div class="pane-title">Single-Turn Review</div>
    <div class="pane-tabs">
      <button id="fixturesTab" class="active">Fixtures</button>
      <button id="queueTab">Queue</button>
    </div>
    <div id="fixtures" class="fixture-list"></div>
    <div id="queue" class="fixture-list hidden"></div>
  </section>
  <section>
    <div class="pane-title">Battle State</div>
    <div id="detail" class="detail"></div>
  </section>
  <section>
    <div class="pane-title">Preference</div>
    <div class="detail">
      <div id="selection" class="meta">No preference selected.</div>
      <label>Pick the better boss choice</label>
      <div id="choices" class="choice-grid"></div>
      <label>Tags for each option</label>
      <div id="reasons"></div>
      <div class="metadata-grid">
        <div>
          <label for="confidence">Confidence</label>
          <select id="confidence"></select>
        </div>
        <div>
          <label for="publicInfoScope">Info scope</label>
          <select id="publicInfoScope"></select>
        </div>
      </div>
      <label for="lessonType">Lesson type</label>
      <select id="lessonType"></select>
      <label>Condition tags</label>
      <div id="conditionTags" class="reason-grid"></div>
      <label class="check-row"><input type="checkbox" id="holdout"> Holdout evaluation row</label>
      <label for="note">Note</label>
      <textarea id="note"></textarea>
      <button class="save" id="save">Save Preference</button>
      <h3>Report</h3>
      <pre id="report"></pre>
    </div>
  </section>
</main>
<script>
const reasonTags = __REASON_TAGS__;
const confidenceOptions = __CONFIDENCE_OPTIONS__;
const publicInfoScopeOptions = __PUBLIC_INFO_SCOPE_OPTIONS__;
const lessonTypeOptions = __LESSON_TYPE_OPTIONS__;
const commonConditionTags = [
  "if_user_faster",
  "if_user_slower",
  "survives_one_hit",
  "ko_confirmed",
  "target_can_punish",
  "target_paralyzed",
  "sleep_clause_free",
  "sleep_clause_occupied",
  "hidden_coverage_plausible",
  "threat_revealed",
  "best_action_not_shown",
  "upstream_switch_issue",
  "scout_before_setup",
  "preserve_ace",
  "mixed_strategy"
];
const trajectoryChoices = __TRAJECTORY_CHOICES__;
const coachConditionTags = [
  "boss_faster",
  "player_faster",
  "survives_one_hit",
  "ko_confirmed",
  "two_hko_only",
  "target_can_punish",
  "target_can_switch",
  "hidden_coverage_plausible",
  "sleep_clause_free",
  "sleep_clause_occupied",
  "preserve_ace",
  "sack_for_clean_switch",
  "do_once_only",
  "repeat_until_ko",
  "rescore_after_switch"
];
const coachBranchTags = [
  "if_player_switches_rescore",
  "if_setup_no_longer_changes_ko_math_attack_now",
  "if_status_landed_do_not_repeat",
  "if_hidden_threat_revealed_preserve",
  "if_clean_switch_available_switch",
  "if_near_tie_preserve_variety"
];
const planTemplates = [
  "do_x_once_then_y",
  "repeat_x_until_stop",
  "set_up_then_cash_damage",
  "scout_probe_then_preserve_or_commit",
  "switch_then_threaten",
  "sack_trade_for_clean_switch",
  "status_then_attack",
  "stall_recover_until_safe"
];
let fixtures = [];
let labelRows = [];
let preferenceRows = [];
let queueRows = [];
let planQueueRows = [];
let trajectoryRows = [];
let demonstrationRows = [];
let currentFixture = null;
let currentPlanCandidate = null;
let currentChoice = null;
let selectedFallbackActionId = null;
let selectedActionTags = {};
let selectedConditionTags = [];
let selectedPlanId = null;
let selectedTrajectoryChoice = null;
let selectedCoachConditionTags = [];
let selectedCoachBranchTags = [];
let showPlanBuilder = false;
let coachConfidenceValue = "medium";
let coachHoldoutValue = false;
let coachNoteText = "";
let coachFilter = "all";
let autoAdvanceCoach = true;
let showAllActions = false;
let leftPanel = "fixtures";
let topPanel = "coach";

function byId(id) { return document.getElementById(id); }
function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}
function valueOrNone(value) {
  if (value === undefined || value === null || value === "") return "none";
  return escapeText(value);
}
function renderFact(label, value) {
  return `<div class="fact"><span>${escapeText(label)}</span><strong>${valueOrNone(value)}</strong></div>`;
}
function renderPills(values) {
  if (!Array.isArray(values) || values.length === 0) return '<span class="meta">none</span>';
  return `<div class="inline-list">${values.map(value => `<span class="tag">${escapeText(value)}</span>`).join("")}</div>`;
}
function selectOptions(values, selectedValue) {
  const options = ['<option value="">unset</option>'];
  values.forEach(value => {
    const selected = selectedValue === value ? " selected" : "";
    options.push(`<option value="${escapeText(value)}"${selected}>${escapeText(value.replaceAll("_", " "))}</option>`);
  });
  return options.join("");
}
function setSelectOptions(id, values, selectedValue) {
  byId(id).innerHTML = selectOptions(values, selectedValue || "");
}
function renderActiveSide(title, side, partyLabel) {
  const active = side.active || {};
  const party = side.bench || side.seen_party || [];
  const publicPriors = active.public_priors || [];
  return `<div class="box">
    <h3>${escapeText(title)}</h3>
    <div class="active-top">
      <div class="pokemon-name">${valueOrNone(active.species)}</div>
      <div class="primary-facts">
        ${renderFact("Level", active.level)}
        ${renderFact("HP", active.hp)}
        ${renderFact("Item", active.item)}
      </div>
    </div>
    <dl class="detail-list">
      <dt>Status</dt><dd>${valueOrNone(active.status)}</dd>
      <dt>Role</dt><dd>${valueOrNone(active.role)}</dd>
      <dt>Revealed moves</dt><dd>${renderPills(active.revealed_moves)}</dd>
      <dt>Public reads</dt><dd>${renderPills(publicPriors)}</dd>
      <dt>${escapeText(partyLabel)}</dt><dd>${renderPills(party)}</dd>
    </dl>
  </div>`;
}
function readableKey(key) {
  return String(key).replaceAll("_", " ");
}
function renderField(field) {
  const rows = Object.entries(field || {});
  const body = rows.length
    ? `<dl class="detail-list">${rows.map(([key, value]) => `<dt>${escapeText(readableKey(key))}</dt><dd>${valueOrNone(value)}</dd>`).join("")}</dl>`
    : '<p class="meta">none</p>';
  return `<div class="box"><h3>Field</h3>${body}</div>`;
}
function renderNotes(notes) {
  if (!Array.isArray(notes) || notes.length === 0) return '<p class="meta">none</p>';
  return `<ul class="note-list">${notes.map(note => `<li>${escapeText(note)}</li>`).join("")}</ul>`;
}
function setupTopTabs() {
  const mapping = [
    ["coachTopTab", "coach"],
    ["queueTopTab", "queue"],
    ["reportsTopTab", "reports"],
    ["dataTopTab", "data"]
  ];
  mapping.forEach(([id, panel]) => {
    byId(id).onclick = () => {
      topPanel = panel;
      if (panel === "queue") coachFilter = "needs_judgment";
      renderTopPanelState();
      renderCoach();
      if (panel === "reports") renderCoachReport();
    };
  });
  const refresh = byId("refreshCoachReport");
  if (refresh) refresh.onclick = renderCoachReport;
  renderTopPanelState();
}
function renderTopPanelState() {
  const visiblePanel = topPanel === "queue" ? "coach" : topPanel;
  byId("coachMain").classList.toggle("hidden", visiblePanel !== "coach");
  byId("reportsMain").classList.toggle("hidden", visiblePanel !== "reports");
  byId("dataMain").classList.toggle("hidden", visiblePanel !== "data");
  [
    ["coachTopTab", "coach"],
    ["queueTopTab", "queue"],
    ["reportsTopTab", "reports"],
    ["dataTopTab", "data"]
  ].forEach(([id, panel]) => byId(id).classList.toggle("active", topPanel === panel));
}
function resetCoachState() {
  selectedPlanId = null;
  selectedTrajectoryChoice = null;
  selectedCoachConditionTags = [];
  selectedCoachBranchTags = [];
  showPlanBuilder = false;
  coachConfidenceValue = "medium";
  coachHoldoutValue = false;
  coachNoteText = "";
}
function captureCoachFormState() {
  const confidence = byId("coachConfidence");
  const holdout = byId("coachHoldout");
  const autoAdvance = byId("coachAutoAdvance");
  const note = byId("coachNote");
  if (confidence) coachConfidenceValue = confidence.value || "medium";
  if (holdout) coachHoldoutValue = holdout.checked;
  if (autoAdvance) autoAdvanceCoach = autoAdvance.checked;
  if (note) coachNoteText = note.value;
}
function fixtureById(fixtureId) {
  return fixtures.find(fixture => fixture.id === fixtureId) || null;
}
function currentCoachFixture() {
  return currentPlanCandidate ? fixtureById(currentPlanCandidate.fixture_id) : null;
}
function planPairKey(fixtureId, planAId, planBId) {
  return [planAId, planBId].sort().join("::") + `::${fixtureId}`;
}
function planPairsForCandidate(candidate) {
  const plans = (candidate && candidate.plans ? candidate.plans : []).slice(0, 4);
  const pairs = [];
  for (let left = 0; left < plans.length; left += 1) {
    for (let right = left + 1; right < plans.length; right += 1) {
      pairs.push([plans[left], plans[right]]);
    }
  }
  return pairs;
}
function savedTrajectoriesForCandidate(candidate) {
  if (!candidate) return [];
  const planIds = new Set((candidate.plans || []).map(plan => plan.id));
  return trajectoryRows.filter(row =>
    row.fixture_id === candidate.fixture_id
    && planIds.has(row.trajectory_a_id)
    && planIds.has(row.trajectory_b_id)
  );
}
function coachCoverageForCandidate(candidate) {
  const requiredPairs = planPairsForCandidate(candidate);
  const savedRows = savedTrajectoriesForCandidate(candidate);
  const savedKeys = new Set(savedRows.map(row =>
    planPairKey(row.fixture_id, row.trajectory_a_id, row.trajectory_b_id)
  ));
  const covered = requiredPairs.filter(([planA, planB]) =>
    savedKeys.has(planPairKey(candidate.fixture_id, planA.id, planB.id))
  ).length;
  return {covered, required: requiredPairs.length, rows: savedRows};
}
function candidateNeedsCoachJudgment(candidate) {
  const coverage = coachCoverageForCandidate(candidate);
  if (!coverage.required) return false;
  return coverage.covered < coverage.required;
}
function savedTrajectoryForCandidate(candidate) {
  const coverage = coachCoverageForCandidate(candidate);
  return coverage.rows[0] || null;
}
function coachFilterOptions() {
  return [
    ["all", "All"],
    ["early", "Early"],
    ["mid", "Mid"],
    ["late", "Late"],
    ["needs_judgment", "Needs my judgment"],
    ["regression_gap", "Regression gap"],
    ["counterfactual", "Counterfactual"],
    ["holdout", "Holdout"]
  ];
}
function candidateMatchesFilter(candidate) {
  if (coachFilter === "all") return true;
  if (["early", "mid", "late"].includes(coachFilter)) return candidate.phase === coachFilter;
  if (coachFilter === "needs_judgment") return candidateNeedsCoachJudgment(candidate);
  const text = `${candidate.candidate_id} ${(candidate.reasons || []).join(" ")} ${(candidate.teaches || []).join(" ")}`.toLowerCase();
  if (coachFilter === "regression_gap") return text.includes("disagree") || text.includes("regression");
  if (coachFilter === "counterfactual") return text.includes("counterfactual") || text.includes("boundary");
  if (coachFilter === "holdout") return text.includes("holdout");
  return true;
}
function renderCoachFilters() {
  byId("coachFilters").innerHTML = coachFilterOptions().map(([value, label]) => {
    const selected = coachFilter === value ? " active" : "";
    return `<button class="${selected}" data-coach-filter="${escapeText(value)}">${escapeText(label)}</button>`;
  }).join("");
  byId("coachFilters").querySelectorAll("[data-coach-filter]").forEach(button => {
    button.onclick = () => {
      coachFilter = button.dataset.coachFilter;
      topPanel = coachFilter === "needs_judgment" ? "queue" : "coach";
      renderTopPanelState();
      renderCoach();
    };
  });
}
function renderCoachQueue() {
  renderCoachFilters();
  const rows = planQueueRows.filter(candidateMatchesFilter);
  if (!rows.length) {
    byId("coachQueue").innerHTML = '<p class="meta">No coach questions match this filter.</p>';
    return;
  }
  byId("coachQueue").innerHTML = rows.map(candidate => {
    const active = currentPlanCandidate && currentPlanCandidate.candidate_id === candidate.candidate_id ? " active" : "";
    const coverage = coachCoverageForCandidate(candidate);
    const saved = coverage.required && coverage.covered >= coverage.required ? " saved" : "";
    const partial = coverage.covered && coverage.covered < coverage.required ? " partial" : "";
    const teaches = (candidate.teaches || []).slice(0, 3).map(tag =>
      `<span class="tag">${escapeText(tag)}</span>`
    ).join("");
    const reasons = (candidate.reasons || []).slice(0, 2).map(reason =>
      `<span class="reason">${escapeText(reason)}</span>`
    ).join("");
    const coverageText = coverage.required ? `${coverage.covered}/${coverage.required} plan pairs saved` : "no plan pairs";
    return `<button class="queue-item fixture-button${active}${saved}${partial}" data-plan-candidate-id="${escapeText(candidate.candidate_id)}">
      <strong>${escapeText(candidate.rank)}. ${escapeText(candidate.leader)} (${escapeText(candidate.priority)})</strong>
      <span>${escapeText(candidate.fixture_id)} | ${escapeText(candidate.phase)} | ${escapeText(coverageText)}</span>
      <div class="tags">${teaches}</div>
      ${reasons}
    </button>`;
  }).join("");
  byId("coachQueue").querySelectorAll("[data-plan-candidate-id]").forEach(button => {
    button.onclick = () => {
      currentPlanCandidate = planQueueRows.find(candidate => candidate.candidate_id === button.dataset.planCandidateId);
      resetCoachState();
      renderCoach();
    };
  });
}
function renderBossKnowledge(fixture) {
  const state = fixture.state || {};
  const boss = state.boss || {};
  const bench = Array.isArray(boss.bench) ? boss.bench : [];
  const actionMoves = (fixture.actions || []).filter(action => action.kind === "move").map(action => action.name);
  const sourceTeam = Array.isArray(fixture.boss_team) ? fixture.boss_team : [];
  const source = fixture.boss_team_source || {};
  const sourceText = source.hash
    ? `${source.group || "team"} #${source.index || "?"} | ${source.hash} | ${source.path || "source"}:${source.line || "?"}`
    : `${source.group || "team source"} | ${source.anchor || "unresolved"}`;
  const teamRows = sourceTeam.length
    ? sourceTeam.map(member => {
      const activeClass = member.active ? " active" : "";
      const activeTag = member.active ? '<span class="tag">active</span>' : '<span class="tag">bench</span>';
      const moves = Array.isArray(member.moves) && member.moves.length ? member.moves.join(" | ") : "moves not listed";
      const hp = member.active ? member.hp : (member.hp === "unknown" ? "not captured" : member.hp);
      const status = member.active ? member.status : (member.status === "unknown" ? "not captured" : member.status);
      const facts = `Lv ${member.level} | HP ${hp} | ${status} | ${member.item}`;
      return `<div class="team-member${activeClass}">
        <div class="team-member-head"><span>${escapeText(member.species)}</span>${activeTag}</div>
        <div class="team-member-facts">${escapeText(facts)}<br>${escapeText(member.role || "")}</div>
        <div class="team-member-moves">${escapeText(moves)}</div>
      </div>`;
    }).join("")
    : bench.map(member => {
      if (typeof member === "object" && member !== null) {
        const moves = Array.isArray(member.moves) ? member.moves.join(" | ") : "moves not in fixture";
        return `<div class="team-member"><div class="team-member-head"><span>${escapeText(member.species || "Bench")}</span><span class="tag">bench</span></div><div class="team-member-moves">${escapeText(moves)}</div></div>`;
      }
      return `<div class="team-member"><div class="team-member-head"><span>${escapeText(member)}</span><span class="tag">bench</span></div><div class="team-member-moves">moves not in this fixture</div></div>`;
    }).join("");
  return `<div class="box team-card">
    <h3>AI Full Team</h3>
    <div class="team-source">${escapeText(sourceText)}</div>
    <dl class="detail-list">
      <dt>Active moves</dt><dd>${renderPills(actionMoves)}</dd>
      <dt>Legal actions</dt><dd>${renderPills((fixture.actions || []).map(action => action.name))}</dd>
    </dl>
    <div class="team-grid" style="margin-top: 8px;">${teamRows || '<p class="meta">No bench listed.</p>'}</div>
  </div>`;
}
function publicMoveBucketsForFixture(fixture) {
  const revealed = (((fixture.state || {}).player || {}).active || {}).revealed_moves || [];
  const revealedLower = new Set(revealed.map(move => String(move).toLowerCase()));
  const plausible = new Set();
  const impossible = new Set();
  (fixture.incoming_threats || []).forEach(threat => {
    const move = threat.move || threat.move_id;
    if (!move || revealedLower.has(String(move).toLowerCase())) return;
    if (threat.likelihood === 0 || threat.bucket === "0%") impossible.add(move);
    else plausible.add(`${move} ${threat.bucket || ""}`.trim());
  });
  const unknownSlots = Math.max(0, 4 - revealed.length);
  return {
    revealed,
    plausible: unknownSlots ? Array.from(plausible).sort() : [],
    impossible: Array.from(impossible).sort(),
    unknown: unknownSlots ? [`${unknownSlots} unrevealed moveslot(s)`] : []
  };
}
function renderPlayerPublicInfo(fixture) {
  const state = fixture.state || {};
  const player = state.player || {};
  const active = player.active || {};
  const buckets = publicMoveBucketsForFixture(fixture);
  return `<div class="box">
    <h3>Player Public Info</h3>
    <div class="active-top">
      <div class="pokemon-name">${valueOrNone(active.species)}</div>
      <div class="primary-facts">
        ${renderFact("Level", active.level)}
        ${renderFact("HP", active.hp)}
        ${renderFact("Item", active.item)}
      </div>
    </div>
    <dl class="detail-list">
      <dt>Status</dt><dd>${valueOrNone(active.status)}</dd>
      <dt>Seen party</dt><dd>${renderPills(player.seen_party)}</dd>
      <dt>Public priors</dt><dd>${renderPills(active.public_priors)}</dd>
    </dl>
    <div class="bucket-grid" style="margin-top: 10px;">
      <div class="bucket-row"><strong>Revealed</strong><span>${renderPills(buckets.revealed)}</span></div>
      <div class="bucket-row"><strong>Plausible</strong><span>${renderPills(buckets.plausible)}</span></div>
      <div class="bucket-row"><strong>Impossible</strong><span>${renderPills(buckets.impossible)}</span></div>
      <div class="bucket-row"><strong>Unknown</strong><span>${renderPills(buckets.unknown)}</span></div>
    </div>
  </div>`;
}
function renderCurrentAiExplanation(candidate) {
  const plans = candidate.plans || [];
  const rows = plans.slice(0, 4).map(plan =>
    `<li>${escapeText(plan.label)} <span class="meta">(${escapeText(plan.shape)}, priority ${escapeText(plan.priority)})</span></li>`
  ).join("");
  return `<div class="box" style="margin-top: 10px;"><h3>Current Plan Generator</h3>
    <ul class="note-list">${rows}</ul>
  </div>`;
}
function renderCoachSnapshot() {
  const fixture = currentCoachFixture();
  if (!fixture || !currentPlanCandidate) {
    byId("coachSnapshot").innerHTML = '<p class="meta">No coach question selected.</p>';
    return;
  }
  const tags = (fixture.tags || []).map(tag => `<span class="tag">${escapeText(tag)}</span>`).join("");
  byId("coachSnapshot").innerHTML = `
    <h2>${escapeText(fixture.leader)} - ${escapeText(fixture.id)}</h2>
    <div class="tags">${tags}<span class="tag">${escapeText(currentPlanCandidate.phase)}</span></div>
    <p>${escapeText(fixture.training_focus || "")}</p>
    <div class="grid">
      ${renderBossKnowledge(fixture)}
      ${renderPlayerPublicInfo(fixture)}
      ${renderField((fixture.state || {}).field)}
    </div>
    <div class="box" style="margin-top: 10px;"><h3>Last Turns / Public Notes</h3>${renderNotes((fixture.state || {}).last_turns || (fixture.state || {}).public_notes)}</div>
    ${renderIncomingThreats(fixture.incoming_threats)}
    ${renderCurrentAiExplanation(currentPlanCandidate)}
  `;
}
function planLetter(index) {
  return String.fromCharCode("A".charCodeAt(0) + index);
}
function renderPlanTimeline(plan) {
  const projection = Array.isArray(plan.projection) ? plan.projection : [];
  if (!projection.length) return "";
  const rows = projection.map(row => {
    const projected = row.projected ? " projected" : "";
    const actor = row.actor && row.actor !== "boss" ? ` <span class="tag">${escapeText(row.actor)}</span>` : "";
    const note = row.projection_note ? `<div class="meta">${escapeText(row.projection_note)}</div>` : "";
    return `<div class="plan-turn${projected}">
      <strong>T${escapeText(row.turn)}</strong>
      <div>
        <div>${escapeText(row.boss_action || "Re-score position")}${actor}</div>
        <div class="meta">${escapeText(row.player_public_response || "")}</div>
        ${note}
      </div>
    </div>`;
  }).join("");
  return `<div class="plan-timeline">${rows}</div>`;
}
function renderPlanCard(plan, index) {
  const selected = selectedPlanId === plan.id ? " selected" : "";
  const stops = (plan.stop_conditions || []).slice(0, 4).join(", ");
  const branches = (plan.branch_rules || []).slice(0, 2).map(rule => `${rule.if} -> ${rule.then}`).join("; ");
  return `<button class="plan-card${selected}" data-plan-id="${escapeText(plan.id)}">
    <div class="plan-title"><span>Plan ${planLetter(index)}: ${escapeText(plan.label)}</span><span><span class="tag">${escapeText(plan.shape)}</span> <span class="tag">${escapeText(plan.horizon || 3)} turns</span></span></div>
    <div class="plan-goal"><strong>Goal:</strong> ${escapeText(plan.goal || "")}</div>
    ${renderPlanTimeline(plan)}
    <div class="plan-stops"><strong>Stops if:</strong> ${escapeText(stops || "plan goal reached")}</div>
    <div class="plan-stops"><strong>Branches:</strong> ${escapeText(branches || "re-score if target switches")}</div>
    <div class="plan-rationale">${escapeText(plan.rationale || "")}</div>
  </button>`;
}
function toggleCoachConditionTag(tag) {
  if (selectedCoachConditionTags.includes(tag)) {
    selectedCoachConditionTags = selectedCoachConditionTags.filter(item => item !== tag);
  } else {
    selectedCoachConditionTags.push(tag);
  }
}
function toggleCoachBranchTag(tag) {
  if (selectedCoachBranchTags.includes(tag)) {
    selectedCoachBranchTags = selectedCoachBranchTags.filter(item => item !== tag);
  } else {
    selectedCoachBranchTags.push(tag);
  }
}
function lessonTypeForCandidate(candidate) {
  const teaches = candidate ? candidate.teaches || [] : [];
  if (teaches.includes("switch_policy")) return "switch_policy";
  if (teaches.includes("scout_policy")) return "scout_policy";
  if (teaches.includes("mixed_strategy")) return "personality_style";
  if (teaches.includes("sequence_policy")) return "sequence_policy";
  return "sequence_policy";
}
function renderCoachChips() {
  const conditionButtons = coachConditionTags.map(tag => {
    const selected = selectedCoachConditionTags.includes(tag) ? " selected" : "";
    return `<button class="chip${selected}" data-coach-condition="${escapeText(tag)}">${escapeText(tag.replaceAll("_", " "))}</button>`;
  }).join("");
  const branchButtons = coachBranchTags.map(tag => {
    const selected = selectedCoachBranchTags.includes(tag) ? " selected" : "";
    return `<button class="chip${selected}" data-coach-branch="${escapeText(tag)}">${escapeText(tag.replaceAll("_", " "))}</button>`;
  }).join("");
  return `<label>Condition chips</label><div class="chip-grid">${conditionButtons}</div>
    <label>Branch / stop chips</label><div class="chip-grid">${branchButtons}</div>`;
}
function builderMoveName(moveName) {
  const text = String(moveName || "").trim();
  return text === "Psychic M" ? "Psychic" : text;
}
function builderMoveActionId(moveName) {
  let text = builderMoveName(moveName).toLowerCase();
  text = text.replace(/['.]/g, "").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return text ? `move_${text}` : "";
}
function activeBossSourceMoves(fixture) {
  const team = Array.isArray(fixture.boss_team) ? fixture.boss_team : [];
  const active = team.find(member => member && member.active);
  return active && Array.isArray(active.moves) ? active.moves : [];
}
function builderActions(fixture) {
  const fixtureActions = Array.isArray(fixture.actions) ? fixture.actions : [];
  const fixtureActionsById = new Map(fixtureActions.map(action => [action.id, action]));
  const actions = [];
  const seen = new Set();
  const addAction = action => {
    if (!action || !action.id || seen.has(action.id)) return;
    seen.add(action.id);
    actions.push(action);
  };
  activeBossSourceMoves(fixture).forEach(move => {
    const id = builderMoveActionId(move);
    if (!id) return;
    addAction(fixtureActionsById.get(id) || {id, kind: "move", name: builderMoveName(move)});
  });
  fixtureActions.forEach(addAction);
  return actions;
}
function actionOptionsForBuilder(fixture, selectedId, allowBlank = false) {
  const options = allowBlank ? ['<option value="">re-score / no forced action</option>'] : [];
  options.push(...builderActions(fixture).map(action => {
    const selected = selectedId === action.id ? " selected" : "";
    return `<option value="${escapeText(action.id)}"${selected}>${escapeText(action.name)}</option>`;
  }));
  return options.join("");
}
function renderPlanBuilder(fixture) {
  if (!showPlanBuilder) return "";
  const actions = Array.isArray(fixture.actions) ? fixture.actions : [];
  const availableActions = builderActions(fixture);
  const first = actions[0] ? actions[0].id : availableActions[0] ? availableActions[0].id : "";
  const second = actions[1] ? actions[1].id : first;
  const turnRows = [1, 2, 3, 4, 5].map(turn => {
    const selected = turn === 1 ? first : turn === 2 ? second : "";
    return `<div class="builder-row"><strong>Turn ${turn}</strong><select id="builderTurn${turn}">${actionOptionsForBuilder(fixture, selected, turn >= 3)}</select></div>`;
  }).join("");
  return `<div class="builder">
    <h3>Missing Plan Builder</h3>
    <label for="builderTemplate">Template</label>
    <select id="builderTemplate">${planTemplates.map(template => `<option value="${escapeText(template)}">${escapeText(template.replaceAll("_", " "))}</option>`).join("")}</select>
    <label for="builderHorizon">Horizon</label>
    <select id="builderHorizon"><option value="3">3 turns</option><option value="4">4 turns</option><option value="5">5 turns</option></select>
    ${turnRows}
  </div>`;
}
function renderCoachAnswer() {
  const fixture = currentCoachFixture();
  const candidate = currentPlanCandidate;
  if (!fixture || !candidate) {
    byId("coachAnswer").innerHTML = '<p class="meta">Pick a coach question first.</p>';
    return;
  }
  const saved = savedTrajectoryForCandidate(candidate);
  const coverage = coachCoverageForCandidate(candidate);
  const plans = candidate.plans || [];
  const choiceButtons = [
    ["both_good", "Shown plans are all fine"],
    ["depends", "Depends between shown plans"],
    ["neither_best_plan_missing", "Best plan missing"],
    ["needs_context", "Needs context"]
  ].map(([choice, label]) => {
    const selected = selectedTrajectoryChoice === choice ? " selected" : "";
    return `<button class="${selected}" data-trajectory-choice="${escapeText(choice)}">${escapeText(label)}</button>`;
  }).join("");
  const savedText = saved
    ? `<div class="saved-summary"><strong>Saved:</strong> ${escapeText(coverage.covered)} / ${escapeText(coverage.required)} shown plan pairs. Latest: ${escapeText(saved.choice)} (${escapeText(saved.created_at || "")})</div>`
    : "";
  byId("coachAnswer").innerHTML = `
    ${savedText}
    <h2>Pick the best plan for ${escapeText(candidate.leader)}</h2>
    <div>${plans.map(renderPlanCard).join("")}</div>
    <div class="coach-actions">${choiceButtons}</div>
    ${renderCoachChips()}
    <label for="coachConfidence">Confidence</label>
    <select id="coachConfidence">${selectOptions(confidenceOptions, coachConfidenceValue)}</select>
    <label class="check-row"><input type="checkbox" id="coachHoldout"${coachHoldoutValue ? " checked" : ""}> Holdout evaluation row</label>
    <label class="check-row"><input type="checkbox" id="coachAutoAdvance"${autoAdvanceCoach ? " checked" : ""}> Auto-advance after save</label>
    <label for="coachNote">Note</label>
    <textarea id="coachNote">${escapeText(coachNoteText)}</textarea>
    ${renderPlanBuilder(fixture)}
    <button class="save" id="saveCoachTrajectory">Save Coach Answer</button>
    <div id="coachSaveStatus" class="meta"></div>
  `;
  byId("coachAnswer").querySelectorAll("[data-plan-id]").forEach(button => {
    button.onclick = () => {
      captureCoachFormState();
      selectedPlanId = button.dataset.planId;
      selectedTrajectoryChoice = "plan_selected";
      showPlanBuilder = false;
      renderCoachAnswer();
    };
  });
  byId("coachAnswer").querySelectorAll("[data-trajectory-choice]").forEach(button => {
    button.onclick = () => {
      captureCoachFormState();
      selectedTrajectoryChoice = button.dataset.trajectoryChoice;
      if (selectedTrajectoryChoice !== "neither_best_plan_missing") selectedPlanId = null;
      showPlanBuilder = selectedTrajectoryChoice === "neither_best_plan_missing";
      renderCoachAnswer();
    };
  });
  byId("coachAnswer").querySelectorAll("[data-coach-condition]").forEach(button => {
    button.onclick = () => {
      captureCoachFormState();
      toggleCoachConditionTag(button.dataset.coachCondition);
      renderCoachAnswer();
    };
  });
  byId("coachAnswer").querySelectorAll("[data-coach-branch]").forEach(button => {
    button.onclick = () => {
      captureCoachFormState();
      toggleCoachBranchTag(button.dataset.coachBranch);
      renderCoachAnswer();
    };
  });
  byId("saveCoachTrajectory").onclick = saveCoachAnswer;
}
function baseTrajectoryBody(candidate, planA, planB, choice, preferred, comparisonScope, comparedPlanIds) {
  return {
    fixture_id: candidate.fixture_id,
    trajectory_a_id: planA.id,
    trajectory_b_id: planB.id,
    choice,
    preferred_trajectory_id: preferred,
    horizon: Math.max(planA.horizon || 3, planB.horizon || 3),
    confidence: byId("coachConfidence").value || "medium",
    public_info_scope: "public_only",
    lesson_type: lessonTypeForCandidate(candidate),
    condition_tags: selectedCoachConditionTags.slice().sort(),
    branch_tags: selectedCoachBranchTags.slice().sort(),
    holdout: byId("coachHoldout").checked,
    comparison_scope: comparisonScope,
    compared_plan_ids: comparedPlanIds.slice().sort(),
    note: byId("coachNote").value
  };
}
function trajectoryBodiesForCoach() {
  const candidate = currentPlanCandidate;
  const plans = candidate ? (candidate.plans || []).slice(0, 4) : [];
  if (!candidate || plans.length < 2) throw new Error("Need at least two generated plans.");
  let choice = selectedTrajectoryChoice;
  const comparedPlanIds = plans.map(plan => plan.id);
  if (choice === "plan_selected") {
    const selected = plans.find(plan => plan.id === selectedPlanId);
    if (!selected) throw new Error("Pick a plan card first.");
    return plans
      .filter(plan => plan.id !== selected.id)
      .map(other => baseTrajectoryBody(
        candidate,
        selected,
        other,
        "a_better",
        selected.id,
        "selected_plan_over_all_shown",
        comparedPlanIds,
      ));
  } else if (!trajectoryChoices.includes(choice)) {
    throw new Error("Pick a plan card or trajectory choice first.");
  }
  return planPairsForCandidate(candidate).map(([planA, planB]) =>
    baseTrajectoryBody(
      candidate,
      planA,
      planB,
      choice,
      null,
      "all_shown_plan_pairs",
      comparedPlanIds,
    )
  );
}
async function saveMissingPlanDemo() {
  const fixture = currentCoachFixture();
  const candidate = currentPlanCandidate;
  if (!fixture || !candidate) return null;
  const horizon = Number(byId("builderHorizon") ? byId("builderHorizon").value : 3) || 3;
  const template = byId("builderTemplate") ? byId("builderTemplate").value : "custom_plan";
  const steps = [];
  for (let turn = 1; turn <= Math.min(5, Math.max(3, horizon)); turn += 1) {
    const select = byId(`builderTurn${turn}`);
    const actionId = select ? select.value : "";
    if (actionId) steps.push({turn, action_id: actionId});
  }
  if (steps.length < 2) throw new Error("Pick at least the first two actions for the missing plan.");
  return await postJson("/api/demonstrations", {
    fixture_id: fixture.id,
    demonstration_id: `demo_${fixture.id}_${Date.now()}`,
    horizon,
    steps,
    near_tie_with: (candidate.plans || []).slice(0, 2).map(plan => plan.id),
    condition_tags: selectedCoachConditionTags.slice().sort(),
    human_summary: byId("coachNote").value || template.replaceAll("_", " ")
  });
}
async function refreshCoachData(candidateId) {
  trajectoryRows = (await fetchJson("/api/trajectories")).trajectories;
  demonstrationRows = (await fetchJson("/api/demonstrations")).demonstrations;
  planQueueRows = (await fetchJson("/api/plan-queue")).candidates;
  currentPlanCandidate = planQueueRows.find(candidate => candidate.candidate_id === candidateId)
    || planQueueRows[0]
    || null;
}
function nextCoachCandidateAfter(candidateId) {
  const visibleRows = planQueueRows.filter(candidateMatchesFilter);
  const unresolved = visibleRows.filter(candidateNeedsCoachJudgment);
  const rows = unresolved.length ? unresolved : visibleRows;
  if (!rows.length) return null;
  const savedIndex = planQueueRows.findIndex(candidate => candidate.candidate_id === candidateId);
  const after = rows.find(candidate =>
    planQueueRows.findIndex(item => item.candidate_id === candidate.candidate_id) > savedIndex
  );
  return after || rows[0];
}
async function saveCoachAnswer() {
  const status = byId("coachSaveStatus");
  const candidateId = currentPlanCandidate ? currentPlanCandidate.candidate_id : null;
  try {
    captureCoachFormState();
    if (selectedTrajectoryChoice === "neither_best_plan_missing") {
      await saveMissingPlanDemo();
    }
    const bodies = trajectoryBodiesForCoach();
    for (const body of bodies) {
      await postJson("/api/trajectories", body);
    }
    await refreshCoachData(candidateId);
    if (autoAdvanceCoach && candidateId) {
      currentPlanCandidate = nextCoachCandidateAfter(candidateId);
    }
    resetCoachState();
    renderCoach();
    await renderCoachReport();
    const afterStatus = byId("coachSaveStatus");
    if (afterStatus) afterStatus.innerHTML = `<span class="ok">Saved ${escapeText(bodies.length)} coach comparison(s).</span>`;
  } catch (error) {
    if (status) status.innerHTML = `<span class="warn">${escapeText(error.message)}</span>`;
  }
}
function renderCoach() {
  if (!currentPlanCandidate && planQueueRows.length) {
    currentPlanCandidate = planQueueRows[0];
  }
  renderCoachQueue();
  renderCoachSnapshot();
  renderCoachAnswer();
  renderTopPanelState();
}
async function renderCoachReport() {
  const coachTarget = byId("coachReport");
  const finalTarget = byId("finalReport");
  if (!coachTarget && !finalTarget) return;
  try {
    if (finalTarget) {
      const finalReport = await fetch("/api/final-report");
      finalTarget.textContent = await finalReport.text();
    }
    if (coachTarget) {
      const report = await fetch("/api/coach-report");
      coachTarget.textContent = await report.text();
    }
  } catch (error) {
    if (coachTarget) coachTarget.textContent = error.stack || error.message;
    if (finalTarget) finalTarget.textContent = error.stack || error.message;
  }
}
function resetPreferenceState() {
  currentChoice = null;
  selectedFallbackActionId = null;
  selectedActionTags = {};
  selectedConditionTags = [];
  showAllActions = false;
}
function savedPreferenceForFixture(fixture) {
  if (!fixture) return null;
  const pair = comparisonPair(fixture);
  if (!pair.a || !pair.b) return null;
  return preferenceRows.find(row =>
    row.fixture_id === fixture.id
    && row.action_a_id === pair.a.id
    && row.action_b_id === pair.b.id
  ) || null;
}
function applySavedPreferenceState() {
  resetPreferenceState();
  const saved = savedPreferenceForFixture(currentFixture);
  if (!saved) {
    byId("note").value = "";
    byId("confidence").value = "";
    byId("publicInfoScope").value = "";
    byId("lessonType").value = "";
    byId("holdout").checked = false;
    return;
  }
  currentChoice = saved.choice || null;
  selectedFallbackActionId = saved.preferred_action_id || null;
  selectedActionTags = {};
  selectedConditionTags = Array.isArray(saved.condition_tags)
    ? saved.condition_tags.slice().sort()
    : [];
  Object.entries(saved.action_tags || {}).forEach(([actionId, tags]) => {
    if (Array.isArray(tags) && tags.length) {
      selectedActionTags[actionId] = tags.slice().sort();
    }
  });
  byId("confidence").value = saved.confidence || "";
  byId("publicInfoScope").value = saved.public_info_scope || "";
  byId("lessonType").value = saved.lesson_type || "";
  byId("holdout").checked = Boolean(saved.holdout);
  byId("note").value = saved.note || "";
}
function comparisonPair(fixture) {
  const baseline = fixture.actions.find(action => action.id === fixture.baseline_action_id) || fixture.actions[0] || null;
  const challenger = fixture.actions.find(action => baseline && action.id !== baseline.id) || null;
  return {a: baseline, b: challenger};
}
function baselineTag(action) {
  return currentFixture && currentFixture.baseline_action_id === action.id ? '<span class="tag">baseline</span>' : "";
}
function renderActionContents(action, candidateLabel) {
  return `
    <div class="candidate-label">${escapeText(candidateLabel)}</div>
    <div class="action-name">${escapeText(action.name)} ${baselineTag(action)}</div>
    <div class="action-kind">${escapeText(action.kind)}</div>
    ${renderDamageEstimate(action)}
    <p>${escapeText(action.explanation)}</p>
    <p class="meta">${escapeText(action.public_tradeoff || "")}</p>
  `;
}
function renderDamageEstimate(action) {
  const estimate = action.damage_estimate;
  if (!estimate) return "";
  const currentHp = estimate.target_hp ? `, target currently ${estimate.target_hp}` : "";
  return `<div class="damage-estimate"><strong>Damage</strong>: ${escapeText(estimate.label)} of max HP vs ${escapeText(estimate.target)}${escapeText(currentHp)} <span class="meta">(${escapeText(estimate.basis)})</span></div>`;
}
function renderIncomingThreats(threats) {
  if (!Array.isArray(threats) || threats.length === 0) {
    return `<div class="box" style="margin-top: 10px;"><h3>Incoming Player Threats</h3><p class="meta">No relevant incoming damaging threats surfaced.</p></div>`;
  }
  const rows = threats.map(threat => {
    const damage = threat.damage
      ? `${escapeText(threat.damage.label)} of max HP into ${escapeText(threat.damage.target)}`
      : "support / no rough damage";
    const entry = threat.entry_risk && threat.entry_risk.damage
      ? ` | switch fit: ${escapeText(threat.switch_fit)} vs ${escapeText(threat.entry_risk.move)} (${escapeText(threat.entry_risk.damage.label)} into ${escapeText(threat.entry_risk.damage.target)})`
      : "";
    const reasons = Array.isArray(threat.reasons) ? threat.reasons.join("; ") : "";
    const sources = Array.isArray(threat.sources) ? threat.sources.join(", ") : "";
    return `<div class="threat">
      <div class="threat-head">
        <div class="threat-name">${escapeText(threat.species)} - ${escapeText(threat.move)}</div>
        <div class="threat-bucket">${escapeText(threat.bucket)}</div>
      </div>
      <div class="threat-details">${escapeText(threat.severity)} | ${escapeText(threat.immediacy)} | ${damage}${entry}</div>
      <div class="threat-details">${escapeText(reasons)} <span class="meta">(${escapeText(sources)})</span></div>
    </div>`;
  }).join("");
  return `<div class="box" style="margin-top: 10px;"><h3>Incoming Player Threats</h3><div class="threat-list">${rows}</div></div>`;
}
function renderCandidateButton(action, candidateLabel, choice) {
  const selected = currentChoice === choice ? " selected" : "";
  return `<button class="action action-card${selected}" data-choice="${choice}">
    ${renderActionContents(action, candidateLabel)}
  </button>`;
}
function renderFallbackButton(action) {
  const selected = selectedFallbackActionId === action.id ? " selected" : "";
  return `<button class="action${selected}" data-fallback-action-id="${escapeText(action.id)}">
    ${renderActionContents(action, "Full action list")}
  </button>`;
}
function renderComparison() {
  const pair = comparisonPair(currentFixture);
  if (!pair.a || !pair.b) {
    return '<div class="box"><h3>Compare</h3><p class="warn">This fixture needs at least two actions.</p></div>';
  }
  const fallback = showAllActions
    ? `<div class="actions">${currentFixture.actions.map(renderFallbackButton).join("")}</div>`
    : "";
  const toggleText = showAllActions ? "Hide full action list" : "Show all actions";
  return `<div class="comparison">
    <h3>Compare Boss Choices</h3>
    <div class="comparison-pair">
      ${renderCandidateButton(pair.a, "Option A", "a_better")}
      ${renderCandidateButton(pair.b, "Option B", "b_better")}
    </div>
    <button class="link-button" id="toggle-actions">${toggleText}</button>
    ${fallback}
  </div>`;
}
function choiceText(choice) {
  return {
    a_better: "A is better",
    b_better: "B is better",
    both_good: "Both are good",
    both_bad: "Both are bad",
    other_better: "A different action is better",
    needs_context: "Can't tell"
  }[choice] || "No preference selected";
}
function actionNameById(fixture, actionId) {
  const action = fixture?.actions?.find(candidate => candidate.id === actionId);
  return action ? action.name : actionId;
}
function savedPreferenceSummary(fixture) {
  const saved = savedPreferenceForFixture(fixture);
  if (!saved) return "";
  const preferred = saved.preferred_action_id
    ? `: ${actionNameById(fixture, saved.preferred_action_id)}`
    : "";
  return `Saved: ${choiceText(saved.choice)}${preferred}`;
}
function preferredActionId() {
  const pair = currentFixture ? comparisonPair(currentFixture) : {a: null, b: null};
  if (currentChoice === "a_better" && pair.a) return pair.a.id;
  if (currentChoice === "b_better" && pair.b) return pair.b.id;
  if (currentChoice === "other_better") return selectedFallbackActionId;
  return null;
}
function selectedTagsFor(actionId) {
  return selectedActionTags[actionId] || [];
}
function toggleActionTag(actionId, tag) {
  const tags = new Set(selectedTagsFor(actionId));
  if (tags.has(tag)) {
    tags.delete(tag);
  } else {
    tags.add(tag);
  }
  if (tags.size) {
    selectedActionTags[actionId] = Array.from(tags).sort();
  } else {
    delete selectedActionTags[actionId];
  }
}
function actionTagsFor(actionIds) {
  const tagsByAction = {};
  actionIds.forEach(actionId => {
    const tags = selectedTagsFor(actionId);
    if (tags.length) tagsByAction[actionId] = tags.slice().sort();
  });
  return tagsByAction;
}
function toggleConditionTag(tag) {
  const tags = new Set(selectedConditionTags);
  if (tags.has(tag)) {
    tags.delete(tag);
  } else {
    tags.add(tag);
  }
  selectedConditionTags = Array.from(tags).sort();
}
function renderMetadataControls() {
  setSelectOptions("confidence", confidenceOptions, byId("confidence").value);
  setSelectOptions("publicInfoScope", publicInfoScopeOptions, byId("publicInfoScope").value);
  setSelectOptions("lessonType", lessonTypeOptions, byId("lessonType").value);
  byId("conditionTags").innerHTML = commonConditionTags.map(tag => {
    const selected = selectedConditionTags.includes(tag) ? " selected" : "";
    return `<button class="reason-button${selected}" data-condition-tag="${escapeText(tag)}">${escapeText(tag.replaceAll("_", " "))}</button>`;
  }).join("");
  byId("conditionTags").querySelectorAll(".reason-button").forEach(button => {
    button.onclick = () => {
      toggleConditionTag(button.dataset.conditionTag);
      renderMetadataControls();
    };
  });
}
function preferenceMetadata() {
  const metadata = {};
  const confidence = byId("confidence").value;
  const publicInfoScope = byId("publicInfoScope").value;
  const lessonType = byId("lessonType").value;
  if (confidence) metadata.confidence = confidence;
  if (publicInfoScope) metadata.public_info_scope = publicInfoScope;
  if (lessonType) metadata.lesson_type = lessonType;
  if (selectedConditionTags.length) metadata.condition_tags = selectedConditionTags.slice().sort();
  if (byId("holdout").checked) metadata.holdout = true;
  return metadata;
}
function renderChoices() {
  const choices = [
    ["a_better", "A is better"],
    ["b_better", "B is better"],
    ["both_good", "Both good"],
    ["both_bad", "Both bad"],
    ["needs_context", "Can't tell"],
  ];
  byId("choices").innerHTML = choices.map(([choice, label]) => {
    const selected = currentChoice === choice ? " selected" : "";
    return `<button class="choice-button${selected}" data-choice="${choice}">${escapeText(label)}</button>`;
  }).join("");
  byId("choices").querySelectorAll(".choice-button").forEach(button => {
    button.onclick = () => {
      currentChoice = button.dataset.choice;
      if (currentChoice !== "other_better") selectedFallbackActionId = null;
      renderDetail();
      renderPreferencePanel();
    };
  });
}
function renderReasons() {
  const pair = currentFixture ? comparisonPair(currentFixture) : {a: null, b: null};
  const actions = [];
  if (pair.a) actions.push(["Option A", pair.a]);
  if (pair.b) actions.push(["Option B", pair.b]);
  const preferred = preferredActionId();
  const preferredAction = preferred
    ? currentFixture.actions.find(action => action.id === preferred)
    : null;
  if (
    currentChoice === "other_better"
    && preferredAction
    && preferredAction.id !== pair.a?.id
    && preferredAction.id !== pair.b?.id
  ) {
    actions.push(["Chosen from full list", preferredAction]);
  }
  byId("reasons").innerHTML = actions.map(([label, action]) => {
    const buttons = reasonTags.map(tag => {
      const selected = selectedTagsFor(action.id).includes(tag) ? " selected" : "";
      return `<button class="reason-button${selected}" data-action-id="${escapeText(action.id)}" data-tag="${escapeText(tag)}">${escapeText(tag.replaceAll("_", " "))}</button>`;
    }).join("");
    return `<div class="reason-block">
      <div class="reason-title">${escapeText(label)} - ${escapeText(action.name)}</div>
      <div class="reason-grid">${buttons}</div>
    </div>`;
  }).join("");
  byId("reasons").querySelectorAll(".reason-button").forEach(button => {
    button.onclick = () => {
      toggleActionTag(button.dataset.actionId, button.dataset.tag);
      renderReasons();
    };
  });
}
function renderPreferencePanel() {
  renderChoices();
  renderReasons();
  renderMetadataControls();
  if (!currentFixture) {
    byId("selection").textContent = "No fixture selected.";
    return;
  }
  const preferred = preferredActionId();
  const preferredAction = preferred
    ? currentFixture.actions.find(action => action.id === preferred)
    : null;
  const suffix = preferredAction ? `: ${preferredAction.name}` : "";
  const currentText = `${choiceText(currentChoice)}${suffix}`;
  const saved = savedPreferenceForFixture(currentFixture);
  if (saved) {
    const savedAt = saved.created_at ? `Last saved: ${saved.created_at}` : "Saved preference";
    byId("selection").innerHTML = `<div class="saved-summary">
      <strong>${escapeText(savedPreferenceSummary(currentFixture))}</strong><br>
      ${escapeText(savedAt)}
    </div>${escapeText(currentText)}`;
  } else {
    byId("selection").textContent = currentText;
  }
}
async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(await response.text());
  return await response.json();
}
async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await response.text());
  return await response.json();
}
async function loadAll() {
  const data = await fetchJson("/api/fixtures");
  fixtures = data.fixtures;
  labelRows = (await fetchJson("/api/labels")).labels;
  preferenceRows = (await fetchJson("/api/preferences")).preferences;
  queueRows = (await fetchJson("/api/active-queue")).candidates;
  planQueueRows = (await fetchJson("/api/plan-queue")).candidates;
  trajectoryRows = (await fetchJson("/api/trajectories")).trajectories;
  demonstrationRows = (await fetchJson("/api/demonstrations")).demonstrations;
  currentFixture = fixtures[0] || null;
  currentPlanCandidate = planQueueRows[0] || null;
  renderMetadataControls();
  applySavedPreferenceState();
  setupTopTabs();
  setupTabs();
  renderCoach();
  renderFixtures();
  renderQueue();
  renderDetail();
  renderPreferencePanel();
  await renderReport();
  await renderCoachReport();
}
function setupTabs() {
  byId("fixturesTab").onclick = () => {
    leftPanel = "fixtures";
    renderLeftPanelState();
  };
  byId("queueTab").onclick = () => {
    leftPanel = "queue";
    renderLeftPanelState();
  };
  renderLeftPanelState();
}
function renderLeftPanelState() {
  byId("fixturesTab").classList.toggle("active", leftPanel === "fixtures");
  byId("queueTab").classList.toggle("active", leftPanel === "queue");
  byId("fixtures").classList.toggle("hidden", leftPanel !== "fixtures");
  byId("queue").classList.toggle("hidden", leftPanel !== "queue");
}
function renderFixtures() {
  byId("summary").textContent = `${fixtures.length} fixtures, ${preferenceRows.length} pairwise, ${trajectoryRows.length} trajectories`;
  byId("fixtures").innerHTML = fixtures.map(fixture => {
    const labelCount = labelRows.filter(row => row.fixture_id === fixture.id).length;
    const preferenceCount = preferenceRows.filter(row => row.fixture_id === fixture.id).length;
    const active = currentFixture && currentFixture.id === fixture.id ? " active" : "";
    const saved = savedPreferenceForFixture(fixture);
    const savedClass = saved ? " saved" : "";
    const savedText = saved ? ` | ${savedPreferenceSummary(fixture)}` : "";
    return `<button class="fixture-button${active}${savedClass}" data-id="${escapeText(fixture.id)}">
      <strong>${escapeText(fixture.leader)}</strong>
      <span>${escapeText(fixture.id)} | ${preferenceCount} preference(s), ${labelCount} label(s)${escapeText(savedText)}</span>
    </button>`;
  }).join("");
  byId("fixtures").querySelectorAll(".fixture-button").forEach(button => {
    button.onclick = () => {
      currentFixture = fixtures.find(fixture => fixture.id === button.dataset.id);
      applySavedPreferenceState();
      renderFixtures();
      renderQueue();
      renderDetail();
      renderPreferencePanel();
    };
  });
  renderLeftPanelState();
}
function renderQueue() {
  if (!queueRows.length) {
    byId("queue").innerHTML = '<p class="meta">No queue candidates.</p>';
    return;
  }
  byId("queue").innerHTML = queueRows.map(candidate => {
    const active = currentFixture && candidate.fixture_id === currentFixture.id ? " active" : "";
    const reasons = (candidate.reasons || []).slice(0, 2).map(reason =>
      `<span class="reason">${escapeText(reason)}</span>`
    ).join("");
    const teaches = (candidate.teaches || []).map(tag =>
      `<span class="tag">${escapeText(tag)}</span>`
    ).join("");
    return `<button class="queue-item fixture-button${active}" data-fixture-id="${escapeText(candidate.fixture_id || "")}">
      <strong>${escapeText(candidate.rank)}. ${escapeText(candidate.leader)} (${escapeText(candidate.priority)})</strong>
      <span>${escapeText(candidate.candidate_id)}</span>
      <div class="tags">${teaches}</div>
      ${reasons}
    </button>`;
  }).join("");
  byId("queue").querySelectorAll("[data-fixture-id]").forEach(button => {
    button.onclick = () => {
      const fixtureId = button.dataset.fixtureId;
      if (!fixtureId) return;
      currentFixture = fixtures.find(fixture => fixture.id === fixtureId) || currentFixture;
      applySavedPreferenceState();
      renderFixtures();
      renderQueue();
      renderDetail();
      renderPreferencePanel();
    };
  });
  renderLeftPanelState();
}
function renderDetail() {
  if (!currentFixture) {
    byId("detail").innerHTML = "";
    return;
  }
  const state = currentFixture.state;
  const tags = (currentFixture.tags || []).map(tag => `<span class="tag">${escapeText(tag)}</span>`).join("");
  byId("detail").innerHTML = `
    <h2>${escapeText(currentFixture.leader)} - ${escapeText(currentFixture.id)}</h2>
    <div class="tags">${tags}</div>
    <p>${escapeText(currentFixture.training_focus || "")}</p>
    <div class="grid">
      ${renderActiveSide("Boss", state.boss, "Bench")}
      ${renderActiveSide("Player", state.player, "Seen party")}
      ${renderField(state.field)}
    </div>
    <div class="box" style="margin-top: 10px;"><h3>Public Notes</h3>${renderNotes(state.public_notes)}</div>
    ${renderIncomingThreats(currentFixture.incoming_threats)}
    ${renderComparison()}
  `;
  byId("detail").querySelectorAll("[data-choice]").forEach(button => {
    button.onclick = () => {
      currentChoice = button.dataset.choice;
      if (currentChoice !== "other_better") selectedFallbackActionId = null;
      renderDetail();
      renderPreferencePanel();
    };
  });
  byId("detail").querySelectorAll("[data-fallback-action-id]").forEach(button => {
    button.onclick = () => {
      selectedFallbackActionId = button.dataset.fallbackActionId;
      const pair = comparisonPair(currentFixture);
      if (pair.a && selectedFallbackActionId === pair.a.id) {
        currentChoice = "a_better";
      } else if (pair.b && selectedFallbackActionId === pair.b.id) {
        currentChoice = "b_better";
      } else {
        currentChoice = "other_better";
      }
      renderDetail();
      renderPreferencePanel();
    };
  });
  const toggle = byId("toggle-actions");
  if (toggle) {
    toggle.onclick = () => {
      showAllActions = !showAllActions;
      renderDetail();
    };
  }
}
async function renderReport() {
  const report = await fetch("/api/report");
  byId("report").textContent = await report.text();
}
byId("save").onclick = async () => {
  const pair = currentFixture ? comparisonPair(currentFixture) : {a: null, b: null};
  if (!currentFixture || !pair.a || !pair.b) {
    byId("selection").innerHTML = '<span class="warn">Select a fixture with two actions first.</span>';
    return;
  }
  if (!currentChoice) {
    byId("selection").innerHTML = '<span class="warn">Pick A, B, both good, both bad, or cannot tell first.</span>';
    return;
  }
  const preferred = preferredActionId();
  if (currentChoice === "other_better" && !preferred) {
    byId("selection").innerHTML = '<span class="warn">Pick the better action from the full action list.</span>';
    return;
  }
  const tagActionIds = [pair.a.id, pair.b.id];
  if (preferred && !tagActionIds.includes(preferred)) tagActionIds.push(preferred);
  const body = {
    fixture_id: currentFixture.id,
    action_a_id: pair.a.id,
    action_b_id: pair.b.id,
    choice: currentChoice,
    preferred_action_id: preferred,
    action_tags: actionTagsFor(tagActionIds),
    note: byId("note").value,
    ...preferenceMetadata()
  };
  try {
    await postJson("/api/preferences", body);
    preferenceRows = (await fetchJson("/api/preferences")).preferences;
    queueRows = (await fetchJson("/api/active-queue")).candidates;
    applySavedPreferenceState();
    renderFixtures();
    renderQueue();
    renderDetail();
    renderPreferencePanel();
    byId("selection").innerHTML = `<span class="ok">Saved preference.</span><br>${byId("selection").innerHTML}`;
    await renderReport();
  } catch (error) {
    byId("selection").innerHTML = `<span class="warn">${escapeText(error.message)}</span>`;
  }
};
loadAll().catch(error => {
  document.body.innerHTML = `<pre>${escapeText(error.stack || error.message)}</pre>`;
});
</script>
</body>
</html>
"""


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
