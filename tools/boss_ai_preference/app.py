from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .damage_estimates import attach_damage_estimates
from .threat_availability import attach_incoming_threats
from .data import (
    ALLOWED_REASON_TAGS,
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
.fixture-list { padding: 8px; }
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
.fixture-button strong { display: block; font-size: 13px; }
.fixture-button span { color: var(--subtle); font-size: 12px; }
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
.reason-grid {
  display: grid;
  gap: 8px;
}
.choice-grid { grid-template-columns: 1fr 1fr; }
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
  main { grid-template-columns: 1fr; height: auto; }
  section { max-height: none; }
}
</style>
</head>
<body>
<header>
  <h1>Boss AI Preference Lab</h1>
  <div id="summary" class="meta"></div>
</header>
<main>
  <section>
    <div class="pane-title">Fixtures</div>
    <div id="fixtures" class="fixture-list"></div>
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
let fixtures = [];
let labelRows = [];
let preferenceRows = [];
let currentFixture = null;
let currentChoice = null;
let selectedFallbackActionId = null;
let selectedActionTags = {};
let showAllActions = false;

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
function resetPreferenceState() {
  currentChoice = null;
  selectedFallbackActionId = null;
  selectedActionTags = {};
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
    return;
  }
  currentChoice = saved.choice || null;
  selectedFallbackActionId = saved.preferred_action_id || null;
  selectedActionTags = {};
  Object.entries(saved.action_tags || {}).forEach(([actionId, tags]) => {
    if (Array.isArray(tags) && tags.length) {
      selectedActionTags[actionId] = tags.slice().sort();
    }
  });
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
  currentFixture = fixtures[0] || null;
  applySavedPreferenceState();
  renderFixtures();
  renderDetail();
  renderPreferencePanel();
  await renderReport();
}
function renderFixtures() {
  byId("summary").textContent = `${fixtures.length} fixtures, ${preferenceRows.length} pairwise preferences, ${labelRows.length} labels`;
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
  document.querySelectorAll(".fixture-button").forEach(button => {
    button.onclick = () => {
      currentFixture = fixtures.find(fixture => fixture.id === button.dataset.id);
      applySavedPreferenceState();
      renderFixtures();
      renderDetail();
      renderPreferencePanel();
    };
  });
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
    note: byId("note").value
  };
  try {
    await postJson("/api/preferences", body);
    preferenceRows = (await fetchJson("/api/preferences")).preferences;
    applySavedPreferenceState();
    renderFixtures();
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
                        {"fixtures": attach_incoming_threats(attach_damage_estimates(fixtures))}
                    )
                elif parsed.path == "/api/labels":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    self._send_json({"labels": labels})
                elif parsed.path == "/api/preferences":
                    fixtures = load_fixtures(fixtures_path)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    self._send_json({"preferences": preferences})
                elif parsed.path == "/api/report":
                    fixtures = load_fixtures(fixtures_path)
                    labels = load_labels(labels_path, fixtures=fixtures)
                    preferences = load_preferences(preferences_path, fixtures=fixtures)
                    self._send_text(
                        render_markdown_report(build_report(fixtures, labels, preferences))
                    )
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "not found")
            except PreferenceDataError as exc:
                self._send_text(str(exc), status=HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in {"/api/labels", "/api/preferences"}:
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
                        fixtures_path=fixtures_path,
                        labels_path=labels_path,
                    )
                    self._send_json({"label": record}, status=HTTPStatus.CREATED)
                else:
                    record = save_preference(
                        fixture_id=body.get("fixture_id", ""),
                        action_a_id=body.get("action_a_id", ""),
                        action_b_id=body.get("action_b_id", ""),
                        choice=body.get("choice", ""),
                        preferred_action_id=body.get("preferred_action_id"),
                        reason_tags=body.get("reason_tags"),
                        action_tags=body.get("action_tags"),
                        note=body.get("note", ""),
                        fixtures_path=fixtures_path,
                        preferences_path=preferences_path,
                    )
                    self._send_json({"preference": record}, status=HTTPStatus.CREATED)
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
            html = HTML.replace("__REASON_TAGS__", json.dumps(ALLOWED_REASON_TAGS))
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
) -> None:
    handler = make_handler(fixtures_path, labels_path, preferences_path)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Boss AI Preference Lab: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Boss AI Preference Lab.")
    finally:
        server.server_close()
