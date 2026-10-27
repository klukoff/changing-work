'use strict';

const $ = id => document.getElementById(id);
const node = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = text;
  if (className) element.className = className;
  return element;
};
const colors = {
  uxr: ['#21665a', '#e6efea'],
  design: ['#496ba0', '#e9eef5'],
  pm: ['#785a90', '#eee9f2'],
  marketing: ['#9b682b', '#f5edde'],
  swe: ['#a35340', '#f4e9e5'],
  software_engineering: ['#a35340', '#f4e9e5'],
};
const facetLabels = {
  work: 'Using AI in the work', workflow: 'Using AI in the work',
  product: 'Working on AI products', enablement: 'Enabling others',
  environment: 'Adapting to AI environments', foundations: 'Foundational capability',
};
const state = { study: null, role: null, view: 'maps', skill: null, filtered: [], review: {}, storageAvailable: true };
const REVIEW_KEY = 'changing-work-public-review-v1';
try { state.review = JSON.parse(localStorage.getItem(REVIEW_KEY) || '{}'); }
catch { state.storageAvailable = false; }

function asText(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(asText).filter(Boolean).join('; ');
  if (typeof value === 'object') return value.text || value.description || value.definition || value.label || '';
  return String(value);
}
function array(value) { return Array.isArray(value) ? value : value ? [value] : []; }
function number(value) { return typeof value === 'number' && Number.isFinite(value) ? value : null; }
function countLabel(value) { return value === null ? '…' : new Intl.NumberFormat('en-US').format(value); }
function pct(count, denominator) { return number(count) !== null && denominator > 0 ? count / denominator * 100 : null; }
function percent(value) { return value === null ? 'n/a' : (value === 0 ? '0' : value.toFixed(1)) + '%'; }
function dateLabel(date) {
  if (!date) return 'October 2026';
  const parsed = new Date(String(date).slice(0, 10) + 'T12:00:00');
  return Number.isNaN(parsed.valueOf()) ? String(date) : parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function safeLink(label, url, className) {
  const a = node('a', label, className);
  if (typeof url === 'string' && /^(https?:\/\/|\.?\.?\/|[a-zA-Z0-9_-]+(?:\/|\.)|#)/.test(url)) {
    a.href = url;
    if (/^https?:/.test(url)) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
  } else { a.href = '#downloads'; }
  return a;
}
function skillStatus(skill) {
  if (number(skill.count) === null) return 'not_assessed';
  const status = (skill.status || state.role?.status || 'candidate').toLowerCase();
  if (/ai.review|context|adjudicat/.test(status)) return 'ai_reviewed';
  if (/human.review|validat/.test(status) && !/unvalid|pending/.test(status)) return 'human_reviewed';
  return 'candidate';
}
function statusLabel(status) {
  return ({ candidate: 'Automated candidate', ai_reviewed: 'AI-reviewed evidence', human_reviewed: 'Human-reviewed evidence', not_assessed: 'Not yet measured' })[status] || 'Provisional evidence';
}
function partialReview(item, denominator) {
  return skillStatus(item) !== 'candidate' && number(item.reviewed_n) !== null && item.reviewed_n < denominator;
}
function measuredPercent(item, denominator) {
  return partialReview(item, denominator) ? null : pct(item.count, denominator);
}
function skillsOf(role) { return (role.branches || []).flatMap(branch => (branch.skills || []).map(skill => ({ ...skill, branch_title: branch.title }))); }
function roleColor(role) { return colors[role.id] || ['#21665a', '#e6efea']; }
function setColor(role) {
  const color = roleColor(role);
  document.documentElement.style.setProperty('--role', color[0]);
  document.documentElement.style.setProperty('--role-light', color[1]);
}

function renderHeader() {
  const data = state.study;
  $('total-ads').textContent = countLabel(data.roles.reduce((sum, role) => sum + (number(role.sample_n) || 0), 0));
  $('total-roles').textContent = data.roles.length;
  $('total-skills').textContent = data.roles.reduce((sum, role) => sum + skillsOf(role).length, 0);
  $('release-date').textContent = dateLabel(data.release?.date);
  $('footer-version').textContent = data.release?.id || data.version || 'Exploratory release · October 2026';
  if (data.repository_url) { $('repository-link').href = data.repository_url; $('repository-link').textContent = 'View the GitHub repository ↗'; }
  if (data.release?.baseline_label) $('baseline-date').textContent = data.release.baseline_label;
}
function renderTabs() {
  $('role-tabs').replaceChildren();
  state.study.roles.forEach(role => {
    const button = node('button', null, 'role-tab');
    button.dataset.role = role.id;
    button.style.setProperty('--tab-color', roleColor(role)[0]);
    button.setAttribute('aria-pressed', String(state.role.id === role.id));
    button.append(node('span', null, 'role-dot'));
    const labels = node('span');
    labels.append(node('span', role.short_label || role.label), node('span', countLabel(number(role.sample_n)) + ' ads', 'tab-n'));
    button.append(labels);
    button.addEventListener('click', () => selectRole(role.id));
    $('role-tabs').append(button);
  });
}
function selectRole(id, updateHash = true) {
  const role = state.study.roles.find(r => r.id === id);
  if (!role) return;
  state.role = role;
  $('skill-search').value = '';
  $('skill-filter').value = 'all';
  setColor(role);
  renderTabs();
  renderRole();
  if (updateHash) history.replaceState(null, '', '#' + id);
}
function renderRole() {
  const role = state.role;
  $('role-index').textContent = 'Occupation ' + String(state.study.roles.indexOf(role) + 1).padStart(2, '0') + ' / ' + String(state.study.roles.length).padStart(2, '0');
  $('role-title').textContent = role.label;
  $('role-description').textContent = role.description || role.scope || 'Explore the activities in this occupational framework. Select any competency to inspect its definition and evidence.';
  $('role-n').textContent = countLabel(number(role.sample_n));
  $('role-skills').textContent = skillsOf(role).length;
  $('role-method-note').textContent = role.methods_note || role.scope || '';
  const skills = skillsOf(role);
  const measured = skills.filter(s => number(s.count) !== null);
  const candidates = measured.some(s => skillStatus(s) === 'candidate');
  $('map-status').textContent = role.measurement_note || (measured.length === 0 ? 'This is an operational taxonomy. Whole-corpus frequencies have not yet been calculated under these definitions.' : candidates ? 'Dashed bars show automated candidate matches in full job descriptions. These are screening results for review, not validated prevalence estimates.' : 'Counts show ads with AI-reviewed supporting evidence. Independent human validation remains pending. Categories may overlap.');
  renderMap();
}
function renderMap() {
  const role = state.role;
  const term = $('skill-search').value.trim().toLowerCase();
  const filter = $('skill-filter').value;
  const allSkills = skillsOf(role);
  const maxPercent = Math.max(0, ...allSkills.map(s => measuredPercent(s, s.n || role.sample_n) || 0));
  const scale = Math.max(10, Math.min(100, Math.ceil(maxPercent / 10) * 10));
  $('map-scale').textContent = allSkills.every(s => partialReview(s, s.n || role.sample_n)) ? 'Supported detections; full-corpus prevalence not established' : allSkills.some(s => number(s.count) !== null) ? 'Bars share a 0–' + scale + '% scale within this map' : '';
  $('map-grid').replaceChildren();
  $('map-grid').classList.toggle('four-branches', role.branches.length === 4);
  state.filtered = [];
  role.branches.forEach((branch, branchIndex) => {
    const matching = (branch.skills || []).filter(skill => {
      const text = [skill.short_id, skill.title, skill.definition, skill.description, branch.title, ...array(skill.facets)].join(' ').toLowerCase();
      return (!term || text.includes(term)) && (filter === 'all' || (filter === 'evidence' && skill.count > 0) || (filter === 'unmeasured' && number(skill.count) === null));
    });
    if (!matching.length) return;
    const section = node('section', null, 'branch');
    const heading = node('div', null, 'branch-head');
    const title = node('h4', branch.title);
    title.id = 'branch-' + branchIndex;
    section.setAttribute('aria-labelledby', title.id);
    heading.append(node('span', String(branchIndex + 1).padStart(2, '0'), 'branch-number'), title);
    section.append(heading);
    if (branch.description || branch.definition) section.append(node('p', branch.description || branch.definition, 'branch-description'));
    const list = node('div', null, 'skill-list');
    matching.forEach(skill => {
      const fullSkill = { ...skill, branch_title: branch.title };
      state.filtered.push(fullSkill);
      const status = skillStatus(skill);
      const denominator = skill.n || role.sample_n;
      const partial = partialReview(skill, denominator);
      const value = measuredPercent(skill, denominator);
      const button = node('button', null, 'skill-node ' + status.replace('_', '-') + (skill.count === 0 ? ' zero' : ''));
      if (status === 'candidate') button.classList.add('candidate');
      if (status === 'not_assessed') button.classList.add('not-assessed');
      if (partial) button.classList.add('partial-review');
      button.dataset.skill = skill.id;
      button.setAttribute('aria-label', (skill.short_id || '') + ' ' + skill.title + '. ' + (partial ? skill.count + ' supporting ads, ' + skill.reviewed_n + ' of ' + denominator + ' ads reviewed' : value === null ? 'Not yet measured' : percent(value) + ', ' + skill.count + ' of ' + denominator + ' ads. ' + statusLabel(status)) + '. Open details.');
      const topline = node('span', null, 'skill-topline');
      topline.append(node('span', skill.short_id || skill.id), node('span', '↗', 'skill-open'));
      topline.lastChild.setAttribute('aria-hidden', 'true');
      const bottom = node('span', null, 'skill-bottom');
      const rate = node('span', partial ? skill.count + ' ads' : value === null ? 'n/a' : percent(value), 'skill-rate');
      if (value !== null) rate.append(node('span', '  ' + skill.count + '/' + denominator, 'skill-denom'));
      const stateText = partial ? 'Supported evidence' : status === 'not_assessed' ? 'Not measured' : skill.count === 0 ? 'Not detected' : status === 'candidate' ? 'Candidate match' : status === 'human_reviewed' ? 'Human-reviewed' : 'AI-reviewed';
      bottom.append(rate, node('span', stateText, 'skill-state'));
      const bar = node('span', null, 'skill-bar');
      bar.setAttribute('aria-hidden', 'true');
      const fill = node('span');
      fill.style.width = Math.min(100, (value || 0) / scale * 100) + '%';
      bar.append(fill);
      button.append(topline, node('span', skill.title, 'skill-title'), bottom, bar);
      button.addEventListener('click', () => openSkill(fullSkill));
      list.append(button);
    });
    section.append(list);
    $('map-grid').append(section);
  });
  $('no-results').hidden = state.filtered.length > 0;
}
function setView(view, updateHash = true) {
  state.view = view;
  const maps = view === 'maps';
  $('map-view').hidden = !maps;
  $('compare-view').hidden = maps;
  $('role-tabs').hidden = !maps;
  $('view-maps').classList.toggle('selected', maps);
  $('view-compare').classList.toggle('selected', !maps);
  $('view-maps').setAttribute('aria-pressed', String(maps));
  $('view-compare').setAttribute('aria-pressed', String(!maps));
  if (updateHash) history.replaceState(null, '', '#' + (maps ? state.role.id : 'compare'));
}
function renderComparison() {
  const data = state.study;
  $('comparison-note').textContent = data.comparison?.note || 'These are provisional automated screens. Read the common definitions and per-role coverage before interpreting differences. Earlier reviewed pilot estimates use different rules and are not combined here.';
  const roleMetrics = new Map(data.roles.map(role => [role.id, array(role.metrics)]));
  let metrics = array(data.comparison?.metrics);
  if (!metrics.length) {
    const seen = new Set();
    data.roles.forEach(role => array(role.metrics).forEach(metric => { if (!seen.has(metric.id)) { metrics.push(metric); seen.add(metric.id); } }));
  }
  $('comparison-grid').replaceChildren();
  if (!metrics.length) {
    $('comparison-grid').append(node('p', 'Harmonized cross-occupation measures are still under review. The individual maps retain their own evidence and measurement status.', 'no-results'));
    return;
  }
  const wrap = node('div', null, 'comparison-table-wrap');
  wrap.tabIndex = 0;
  wrap.setAttribute('role', 'region');
  wrap.setAttribute('aria-label', 'AI expectation comparison table, scroll horizontally on smaller screens');
  const table = node('table', null, 'comparison-table');
  const head = node('thead');
  const headRow = node('tr');
  const firstHeader = node('th', 'AI relationship'); firstHeader.scope = 'col'; headRow.append(firstHeader);
  data.roles.forEach(role => {
    const th = node('th', role.short_label || role.label);
    th.scope = 'col';
    th.append(node('span', 'n = ' + countLabel(role.sample_n), 'metric-note'));
    headRow.append(th);
  });
  head.append(headRow); table.append(head);
  const body = node('tbody');
  metrics.forEach(metric => {
    const row = node('tr');
    const th = node('th', metric.label || metric.title || metric.id); th.scope = 'row';
    if (metric.description || metric.note) th.append(node('span', metric.description || metric.note, 'metric-note'));
    row.append(th);
    data.roles.forEach(role => {
      const match = roleMetrics.get(role.id).find(m => m.id === metric.id) || metric.values?.[role.id] || {};
      const count = number(match.count);
      const n = match.n || role.sample_n;
      const status = skillStatus({ ...match, count, status: match.status || metric.status || 'candidate' });
      const partial = partialReview({ ...match, count, status }, n);
      const value = measuredPercent({ ...match, count, status }, n);
      const td = node('td', null, status === 'candidate' ? 'candidate' : '');
      td.style.setProperty('--cell-color', roleColor(role)[0]);
      td.append(node('span', partial ? count + ' ads' : percent(value), 'compare-value'));
      td.append(node('span', partial ? match.reviewed_n + ' of ' + countLabel(n) + ' ads reviewed' : count === null ? 'Not yet measured' : count + ' of ' + countLabel(n) + ' ads', 'compare-n'));
      if (value !== null) {
        const bar = node('div', null, 'comparison-bar'); bar.setAttribute('aria-hidden', 'true');
        const fill = node('span'); fill.style.width = Math.min(100, value) + '%'; bar.append(fill); td.append(bar);
        td.append(node('span', statusLabel(status), 'compare-status'));
      }
      row.append(td);
    });
    body.append(row);
  });
  table.append(body); wrap.append(table); $('comparison-grid').append(wrap);
}

function sectionWithList(title, values) {
  const items = array(values).map(asText).filter(Boolean);
  if (!items.length) return null;
  const section = node('section', null, 'detail-section');
  section.append(node('h3', title));
  const list = node('ul'); items.forEach(text => list.append(node('li', text))); section.append(list);
  return section;
}
function openSkill(skill, updateHash = true) {
  state.skill = skill;
  const status = skillStatus(skill);
  const denominator = skill.n || state.role.sample_n;
  const partial = partialReview(skill, denominator);
  const value = measuredPercent(skill, denominator);
  $('detail-occupation').textContent = state.role.label + ' / ' + skill.branch_title;
  $('detail-id').textContent = skill.short_id || skill.id;
  $('detail-title').textContent = skill.title;
  $('detail-definition').textContent = skill.definition || skill.operational_definition || skill.description || 'This competency is part of the working framework. Its operational definition is being refined.';
  $('detail-measure').replaceChildren();
  const measure = node('div', null, 'detail-measure');
  measure.append(node('span', partial ? skill.count + ' ads' : percent(value), 'big-number'));
  const measureText = node('p', partial ? skill.count + ' supporting ads identified among ' + skill.reviewed_n + ' reviewed. ' + countLabel(denominator) + ' ads in the full cohort.' : value === null ? 'Whole-corpus frequency not yet measured.' : skill.count + ' of ' + countLabel(denominator) + ' ads');
  measureText.append(node('small', statusLabel(status) + (partial ? ' · Review is incomplete. This is not a whole-cohort prevalence estimate.' : status === 'not_assessed' ? ' · A category is not evidence of prevalence.' : ' · Multiple mentions in one ad count once.')));
  if (!partial && number(skill.reviewed_n) !== null) measureText.append(node('small', 'Review coverage: ' + skill.reviewed_n + ' ads' + (number(skill.reviewed_positive_count) !== null ? ', including ' + skill.reviewed_positive_count + ' supporting cases' : '') + '. This coverage does not replace the automated count.'));
  measure.append(measureText); $('detail-measure').append(measure);
  $('detail-facets').replaceChildren();
  const facets = array(skill.facets || skill.facet);
  facets.forEach(facet => $('detail-facets').append(node('span', facetLabels[facet] || facet)));
  $('detail-rules').replaceChildren();
  for (const [title, field] of [['Include when', 'include_when'], ['Exclude when', 'exclude_when'], ['Minimum evidence', 'minimum_evidence']]) {
    const section = sectionWithList(title, skill[field] || skill.coding_guidance?.[field]);
    if (section) $('detail-rules').append(section);
  }
  if (skill.note || skill.measurement_note) {
    const section = node('div', null, 'detail-section'); section.append(node('h3', 'Interpretation'), node('p', skill.note || skill.measurement_note)); $('detail-rules').append(section);
  }
  $('detail-evidence').replaceChildren();
  const evidenceSection = node('section', null, 'detail-section');
  evidenceSection.append(node('h3', 'Evidence to inspect'));
  const examples = array(skill.evidence);
  if (!examples.length) evidenceSection.append(node('p', value === null ? 'No public excerpt is attached to this category yet. Its presence in the framework does not establish how often it occurs.' : skill.count === 0 ? 'No supporting match was detected under this coding procedure. This is not proof that the activity is absent from workplaces.' : 'The public release currently provides aggregate matches for this category. Source-level review remains part of the validation process.'));
  examples.forEach(example => {
    const item = node('div', null, 'evidence-item');
    if (example.quote) item.append(node('blockquote', example.quote));
    item.append(node('p', [example.employer, example.title].filter(Boolean).join(' · ') || 'Source job advertisement', 'evidence-meta'));
    if (example.context || example.status) item.append(node('p', [example.context, example.status].filter(Boolean).join(' · '), 'evidence-context'));
    if (example.source_url || example.url) item.append(safeLink('Open the original source ↗', example.source_url || example.url));
    evidenceSection.append(item);
  });
  if (examples.length) evidenceSection.append(node('p', 'Excerpts illustrate the coding and are not a representative sample of every match. Source links may refer to closed vacancies.'));
  $('detail-evidence').append(evidenceSection);
  const key = state.role.id + '/' + skill.id;
  $('feedback-decision').value = state.review[key]?.decision || '';
  $('feedback-note').value = state.review[key]?.note || '';
  $('feedback-state').textContent = state.review[key] ? 'Saved in this browser' : '';
  const allSkills = skillsOf(state.role);
  const index = allSkills.findIndex(s => s.id === skill.id);
  $('detail-position').textContent = (index + 1) + ' of ' + allSkills.length + ' competencies';
  $('previous-skill').disabled = index <= 0;
  $('next-skill').disabled = index >= allSkills.length - 1;
  if (updateHash) history.replaceState(null, '', '#' + state.role.id + '/' + (skill.short_id || skill.id));
  if (!$('skill-dialog').open) $('skill-dialog').showModal();
  $('skill-dialog').scrollTop = 0;
}
function closeSkill() {
  $('skill-dialog').close();
  state.skill = null;
  history.replaceState(null, '', '#' + state.role.id);
}
function moveSkill(direction) {
  const all = skillsOf(state.role);
  const index = all.findIndex(s => s.id === state.skill?.id);
  if (all[index + direction]) openSkill(all[index + direction]);
}
function saveFeedback() {
  if (!state.skill) return;
  const key = state.role.id + '/' + state.skill.id;
  state.review[key] = { role: state.role.id, competency_id: state.skill.id, short_id: state.skill.short_id, title: state.skill.title, decision: $('feedback-decision').value, note: $('feedback-note').value, release: state.study.release?.id || state.study.version, updated_at: new Date().toISOString() };
  try { localStorage.setItem(REVIEW_KEY, JSON.stringify(state.review)); state.storageAvailable = true; $('feedback-state').textContent = 'Saved in this browser'; }
  catch { state.storageAvailable = false; $('feedback-state').textContent = 'Browser storage unavailable. Export to keep your note.'; }
}
function exportFeedback() {
  saveFeedback();
  const blob = new Blob([JSON.stringify({ project: 'Changing Work', note: 'User-authored review notes. Not submitted to the research team.', exported_at: new Date().toISOString(), reviews: Object.values(state.review) }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'changing-work-review-' + new Date().toISOString().slice(0, 10) + '.json'; document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderMethods() {
  const methods = state.study.methods || {};
  if (methods.summary) $('methods-summary').textContent = methods.summary;
  const defaults = [
    { title: 'Collect full descriptions', description: 'Recover job-ad text from a pinned public source. Preserve source dates, identifiers, and version information.' },
    { title: 'Define the occupations', description: 'Use role responsibilities and documented eligibility rules. AI wording is not required for inclusion.' },
    { title: 'Code explicit evidence', description: 'Apply defined competencies and AI relationships to full ads. Keep automated candidates distinct from reviewed interpretations.' },
    { title: 'Review and reproduce', description: 'Inspect boundaries and negative cases, preserve earlier releases, and expose the data behind every displayed count.' },
  ];
  $('method-steps').replaceChildren();
  array(methods.steps?.length ? methods.steps : defaults).forEach(step => {
    const li = node('li');
    li.append(node('h3', step.title || step.label || 'Study step'), node('p', step.description || step.text || asText(step)));
    $('method-steps').append(li);
  });
  const limitations = methods.limitations?.length ? methods.limitations : [
    'Independent human validation of screening and coding remains incomplete.',
    'Source and employer coverage do not represent all US vacancies.',
    'Advertised expectations do not establish actual AI use, productivity, or causal change.',
    'Known posting dates and unknown dates are retained separately. Closed ads can be included.',
  ];
  $('limitations').replaceChildren(); array(limitations).forEach(item => $('limitations').append(node('li', asText(item))));
  $('methods-links').replaceChildren();
  array(methods.links).forEach(item => $('methods-links').append(safeLink(item.label + ' ↗', item.url)));
  if (state.study.monitoring?.summary) $('monitor-summary').textContent = state.study.monitoring.summary;
  if (state.study.monitoring?.note) $('monitoring-detail').textContent = state.study.monitoring.note;
}
function renderDownloads() {
  const downloads = array(state.study.downloads);
  if (!downloads.some(d => d.url === 'data/study.json')) downloads.unshift({ label: 'Public study data', url: 'data/study.json', description: 'Counts, map definitions, evidence excerpts, and release metadata · JSON' });
  $('download-list').replaceChildren();
  downloads.forEach(item => {
    const link = safeLink(null, item.url, 'download-item');
    const content = node('span'); content.append(node('strong', item.label || item.title), node('small', item.description || 'Download research artifact'));
    link.append(content, node('span', '↗', 'download-arrow')); $('download-list').append(link);
  });
  $('source-list').replaceChildren();
  array(state.study.sources).forEach(source => { const li = node('li'); li.append(safeLink(source.label || source.title || source.url, source.url)); $('source-list').append(li); });
}
function readRoute() {
  if (!state.study) return;
  const parts = location.hash.slice(1).split('/');
  const role = state.study.roles.find(r => r.id === parts[0]);
  if (parts[0] === 'compare') { setView('compare', false); return; }
  if (role) {
    setView('maps', false); selectRole(role.id, false);
    if (parts[1]) {
      const skill = skillsOf(role).find(s => s.short_id === decodeURIComponent(parts[1]) || s.id === decodeURIComponent(parts[1]));
      if (skill) openSkill(skill, false);
    }
  }
}

$('skill-search').addEventListener('input', renderMap);
$('skill-filter').addEventListener('change', renderMap);
$('view-maps').addEventListener('click', () => setView('maps'));
$('view-compare').addEventListener('click', () => setView('compare'));
$('close-dialog').addEventListener('click', closeSkill);
$('skill-dialog').addEventListener('cancel', event => { event.preventDefault(); closeSkill(); });
$('skill-dialog').addEventListener('click', event => { if (event.target === $('skill-dialog')) { const box = $('skill-dialog').getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closeSkill(); } });
$('previous-skill').addEventListener('click', () => moveSkill(-1));
$('next-skill').addEventListener('click', () => moveSkill(1));
$('feedback-decision').addEventListener('change', saveFeedback);
$('feedback-note').addEventListener('input', saveFeedback);
$('export-feedback').addEventListener('click', exportFeedback);
window.addEventListener('hashchange', readRoute);

fetch('data/study.json').then(response => {
  if (!response.ok) throw new Error('Study data could not be loaded (' + response.status + ').');
  return response.json();
}).then(data => {
  if (!Array.isArray(data.roles) || !data.roles.length) throw new Error('The release does not contain any occupational maps.');
  state.study = data;
  state.role = data.roles[0];
  renderHeader(); selectRole(state.role.id, false); renderComparison(); renderMethods(); renderDownloads();
  $('load-status').hidden = true; $('exploration').hidden = false;
  readRoute();
}).catch(error => {
  $('load-status').classList.add('error');
  $('load-status').textContent = 'The study could not load. Please reload this page or open the public data download. ' + error.message;
});
