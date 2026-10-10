/**
 * MetaOracle Web Application Controller
 * Handles application state, user interactions, tabs, and dynamic components.
 */

// Application State
const state = {
  activeTab: 'dashboard',
  presets: [],
  relations: [],
  selectedRelationIds: new Set(),
  activeTestRun: null,
  activeMutationRun: null,
  activeBenchmarkRun: null,
  snippets: [],
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', async () => {
  initTabNavigation();
  initEventListeners();
  await checkBackendConnection();
  await loadInitialData();
});

/**
 * Backend Connection & Health Check
 */
async function checkBackendConnection() {
  const statusPill = document.getElementById('connection-status-pill');
  try {
    const health = await window.api.getHealth();
    if (statusPill) {
      statusPill.innerHTML = `
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 mr-2 live-pulse"></span>
        <span class="text-xs font-semibold text-emerald-400">Backend Connected • SQLite Online</span>
      `;
    }
  } catch (err) {
    if (statusPill) {
      statusPill.innerHTML = `
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-rose-500 mr-2"></span>
        <span class="text-xs font-semibold text-rose-400">Disconnected • Server Offline</span>
      `;
    }
    showToast('Failed to connect to MetaOracle backend. Ensure backend server is running.', 'danger');
  }
}

/**
 * Load Presets, Relations, and Dashboard Stats
 */
async function loadInitialData() {
  try {
    // 1. Fetch presets
    state.presets = await window.api.getPresets();
    populatePresetDropdowns();

    // 2. Fetch relations catalog
    state.relations = await window.api.getRelations();
    renderRelationsCatalog(state.relations);
    populateRelationsChecklist();

    // 3. Load Dashboard Stats
    await refreshDashboard();

    // 4. Load Snippets
    await loadSnippets();

    // 5. Load History
    await loadHistory();
  } catch (err) {
    console.error('Initialization error:', err);
  }
}

/**
 * Tab Navigation Router
 */
function initTabNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = tab.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Handle URL hash if present
  const hash = window.location.hash.replace('#', '');
  if (hash && document.getElementById(`tab-${hash}`)) {
    switchTab(hash);
  }
}

function switchTab(tabId) {
  state.activeTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.nav-tab').forEach(tab => {
    if (tab.getAttribute('data-tab') === tabId) {
      tab.classList.add('active', 'border-indigo-500', 'text-indigo-400', 'bg-indigo-950/40');
      tab.classList.remove('text-slate-400', 'border-transparent');
    } else {
      tab.classList.remove('active', 'border-indigo-500', 'text-indigo-400', 'bg-indigo-950/40');
      tab.classList.add('text-slate-400', 'border-transparent');
    }
  });

  // Toggle Tab Sections
  document.querySelectorAll('.tab-section').forEach(section => {
    if (section.id === `tab-${tabId}`) {
      section.classList.remove('hidden');
    } else {
      section.classList.add('hidden');
    }
  });

  window.location.hash = tabId;

  // Trigger tab-specific refresh
  if (tabId === 'dashboard') refreshDashboard();
  if (tabId === 'history') loadHistory();
  if (tabId === 'snippets') loadSnippets();
}

/**
 * Presets Population & Code Mirror Sync
 */
function populatePresetDropdowns() {
  const categorySelect = document.getElementById('studio-category-select');
  const variantSelect = document.getElementById('studio-variant-select');
  if (!categorySelect || !variantSelect) return;

  const categories = [...new Set(state.presets.map(p => p.category))];
  categories.push('Custom Python Code');

  categorySelect.innerHTML = categories
    .map(c => `<option value="${c}">${c}</option>`)
    .join('');

  updateVariantOptions();
}

function updateVariantOptions() {
  const categorySelect = document.getElementById('studio-category-select');
  const variantSelect = document.getElementById('studio-variant-select');
  const selectedCat = categorySelect.value;

  if (selectedCat === 'Custom Python Code') {
    variantSelect.innerHTML = `<option value="Custom Function">User Defined Implementation</option>`;
    onPresetSelectionChange();
    return;
  }

  const matchingPresets = state.presets.filter(p => p.category === selectedCat);
  variantSelect.innerHTML = matchingPresets
    .map(p => `<option value="${p.variant}">${p.variant}</option>`)
    .join('');

  onPresetSelectionChange();
}

function onPresetSelectionChange() {
  const category = document.getElementById('studio-category-select').value;
  const variant = document.getElementById('studio-variant-select').value;
  const codeArea = document.getElementById('studio-code-editor');
  const descBox = document.getElementById('studio-preset-desc');
  const inputTypeSelect = document.getElementById('studio-input-type');

  if (category === 'Custom Python Code') {
    if (!codeArea.value.trim() || codeArea.value.includes('def sort_list') || codeArea.value.includes('def shortest_route')) {
      codeArea.value = `def custom_function(items):\n    """Custom function to test with metamorphic relations."""\n    if not items:\n        return []\n    return sorted(items)\n`;
    }
    if (descBox) descBox.textContent = 'Custom Python code entered directly by developer.';
    if (inputTypeSelect) inputTypeSelect.value = 'list';
    return;
  }

  const preset = state.presets.find(p => p.category === category && p.variant === variant);
  if (preset) {
    codeArea.value = preset.code || '';
    if (descBox) descBox.textContent = preset.description || '';
    if (inputTypeSelect) inputTypeSelect.value = preset.input_type || 'list';
  }
}

/**
 * Populate Relations Checklist in Studio
 */
function populateRelationsChecklist() {
  const container = document.getElementById('studio-relations-checklist');
  if (!container) return;

  container.innerHTML = state.relations.map(rel => {
    return `
      <label class="flex items-start p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/60 cursor-pointer transition">
        <input type="checkbox" value="${rel.relation_id}" class="mt-1 mr-3 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 relation-check-input" checked>
        <div class="flex-1">
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-slate-200">${escapeHtml(rel.name)}</span>
            <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-indigo-400">${escapeHtml(rel.category)}</span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5 line-clamp-1">${escapeHtml(rel.description)}</p>
          <div class="text-[11px] font-mono text-cyan-400 mt-1">${escapeHtml(rel.formula || '')}</div>
        </div>
      </label>
    `;
  }).join('');
}

/**
 * Auto-Suggest Relations via AST Analysis
 */
async function triggerAutoSuggest() {
  const category = document.getElementById('studio-category-select').value;
  const variant = document.getElementById('studio-variant-select').value;
  const code = document.getElementById('studio-code-editor').value;
  const suggestBtn = document.getElementById('btn-auto-suggest');

  suggestBtn.disabled = true;
  suggestBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⚙️</span> Analyzing AST...`;

  try {
    const res = await window.api.suggestRelations({
      category: category,
      variant: variant,
      code: code,
    });

    const suggestedIds = new Set(res.suggestions.map(s => s.relation_id));

    // Update checkboxes
    const checkboxes = document.querySelectorAll('.relation-check-input');
    checkboxes.forEach(cb => {
      cb.checked = suggestedIds.has(cb.value);
    });

    // Render suggestion notifications banner
    const banner = document.getElementById('studio-suggest-banner');
    if (banner) {
      banner.classList.remove('hidden');
      banner.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <h4 class="text-sm font-bold text-indigo-300 flex items-center">
            <span class="mr-2">💡</span> AST Recommender: Suggested ${res.suggestions.length} Metamorphic Relations
          </h4>
          <button onclick="document.getElementById('studio-suggest-banner').classList.add('hidden')" class="text-slate-400 hover:text-white text-xs">✕ Dismiss</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
          ${res.suggestions.map(s => `
            <div class="p-2 rounded bg-indigo-950/40 border border-indigo-800/40 text-xs">
              <div class="flex justify-between font-semibold text-slate-200">
                <span>${escapeHtml(s.relation_name)}</span>
                <span class="text-emerald-400 font-mono text-[10px]">${s.confidence} Confidence</span>
              </div>
              <p class="text-slate-400 mt-1">${escapeHtml(s.rationale)}</p>
            </div>
          `).join('')}
        </div>
      `;
    }

    showToast(`AST analysis completed! ${res.suggestions.length} relations recommended and checked.`, 'success');
  } catch (err) {
    showToast(`Failed to suggest relations: ${err.message}`, 'danger');
  } finally {
    suggestBtn.disabled = false;
    suggestBtn.innerHTML = `<span>✨</span> Auto-Suggest Relations (AST)`;
  }
}

/**
 * Execute Metamorphic Test Suite
 */
async function runMetamorphicStudioTests() {
  const category = document.getElementById('studio-category-select').value;
  const variant = document.getElementById('studio-variant-select').value;
  const code = document.getElementById('studio-code-editor').value;
  const inputType = document.getElementById('studio-input-type').value;
  const budget = parseInt(document.getElementById('studio-budget-slider').value, 10);
  const runBtn = document.getElementById('btn-run-tests');

  // Collect checked relations
  const selectedIds = [];
  document.querySelectorAll('.relation-check-input:checked').forEach(cb => {
    selectedIds.push(cb.value);
  });

  if (selectedIds.length === 0) {
    showToast('Please select at least one Metamorphic Relation to test.', 'warning');
    return;
  }

  runBtn.disabled = true;
  runBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⚙️</span> Executing Suite (${budget} tests)...`;

  try {
    const payload = {
      category: category,
      variant: variant,
      custom_code: code,
      input_type: inputType,
      selected_relation_ids: selectedIds,
      test_budget: budget,
      seed: 42,
    };

    const report = await window.api.runTests(payload);
    state.activeTestRun = report;

    // Render results in Studio
    renderStudioResults(report);
    showToast(`Metamorphic tests complete! Tested ${report.total_tests} cases.`, report.status === 'PASSED' ? 'success' : 'warning');
  } catch (err) {
    showToast(`Test execution failed: ${err.message}`, 'danger');
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `<span>⚡</span> Run Metamorphic Suite`;
  }
}

/**
 * Render Metamorphic Test Results
 */
function renderStudioResults(report) {
  const resultsContainer = document.getElementById('studio-results-container');
  resultsContainer.classList.remove('hidden');

  // Status Banner
  const isViolated = report.status === 'VIOLATED';
  const statusColor = isViolated ? 'border-amber-500/50 bg-amber-950/20 text-amber-300' : 'border-emerald-500/50 bg-emerald-950/20 text-emerald-300';
  const statusIcon = isViolated ? '⚠️' : '✅';
  const statusTitle = isViolated ? 'Metamorphic Violations Detected (Bug Exposed!)' : 'All Metamorphic Relations Satisfied';

  document.getElementById('studio-summary-banner').className = `p-4 rounded-xl border ${statusColor} mb-6`;
  document.getElementById('studio-summary-banner').innerHTML = `
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <span class="text-3xl">${statusIcon}</span>
        <div>
          <h3 class="text-lg font-bold">${statusTitle}</h3>
          <p class="text-xs text-slate-400 mt-0.5">Target: <span class="font-mono text-slate-200">${escapeHtml(report.function_name)}</span> • Run ID: #${report.id}</p>
        </div>
      </div>
      <div class="flex items-center space-x-6 text-right">
        <div>
          <div class="text-2xl font-black font-mono ${isViolated ? 'text-amber-400' : 'text-emerald-400'}">${report.pass_rate}%</div>
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Pass Rate</div>
        </div>
        <div>
          <div class="text-2xl font-black font-mono text-slate-200">${report.total_tests}</div>
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Total Tests</div>
        </div>
        <div>
          <div class="text-2xl font-black font-mono text-rose-400">${report.violated_tests}</div>
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Violations</div>
        </div>
        <div>
          <div class="text-2xl font-black font-mono text-slate-200">${report.duration_ms}ms</div>
          <div class="text-[11px] uppercase tracking-wider text-slate-400">Duration</div>
        </div>
      </div>
    </div>
  `;

  // Relation Breakdown Cards
  const breakdownContainer = document.getElementById('studio-relation-breakdown');
  const relSummary = report.relation_summary || {};
  const relEntries = Object.entries(relSummary);

  breakdownContainer.innerHTML = relEntries.map(([rid, rdata]) => {
    const relPassed = rdata.violated_tests === 0;
    const badgeColor = relPassed ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40' : 'text-rose-400 bg-rose-950/40 border-rose-800/40';
    return `
      <div class="p-3.5 rounded-lg border border-slate-800 bg-slate-900/80">
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-slate-200">${escapeHtml(rdata.relation_name)}</span>
          <span class="text-xs px-2 py-0.5 rounded font-mono border ${badgeColor}">${rdata.pass_rate}% Pass</span>
        </div>
        <div class="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
          <div class="bg-indigo-500 h-1.5 rounded-full" style="width: ${rdata.pass_rate}%"></div>
        </div>
        <div class="flex justify-between text-xs text-slate-400 mt-2">
          <span>Passed: <strong class="text-slate-200">${rdata.passed_tests}</strong></span>
          <span>Violations: <strong class="${rdata.violated_tests > 0 ? 'text-rose-400' : 'text-slate-200'}">${rdata.violated_tests}</strong></span>
          <span>Errors: <strong class="text-slate-200">${rdata.error_tests}</strong></span>
        </div>
      </div>
    `;
  }).join('');

  // Counterexample Explorer
  const counterexamplesContainer = document.getElementById('studio-counterexamples-list');
  const testCases = report.test_cases || [];
  const violations = testCases.filter(tc => tc.is_violation);

  if (violations.length === 0) {
    counterexamplesContainer.innerHTML = `
      <div class="p-6 text-center text-slate-400 border border-dashed border-slate-800 rounded-xl">
        <span class="text-2xl">✨</span>
        <p class="mt-2 text-sm">No counterexamples found! All metamorphic invariant checks satisfied.</p>
      </div>
    `;
  } else {
    counterexamplesContainer.innerHTML = violations.map((ce, index) => {
      return `
        <div class="p-4 rounded-xl border border-rose-900/50 bg-rose-950/15 mb-4">
          <div class="flex items-center justify-between border-b border-rose-900/30 pb-2 mb-3">
            <div class="flex items-center space-x-2">
              <span class="px-2 py-0.5 rounded bg-rose-900/40 text-rose-300 font-mono text-xs font-bold">Counterexample #${index + 1}</span>
              <span class="text-sm font-semibold text-slate-200">${escapeHtml(ce.relation_name)}</span>
            </div>
            <span class="text-xs font-mono text-slate-400">${ce.duration_ms}ms</span>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <!-- Source Pair -->
            <div class="p-3 rounded bg-slate-900/80 border border-slate-800">
              <div class="text-indigo-400 font-bold mb-1">Source Execution:</div>
              <div class="text-slate-400">Input <span class="text-slate-500 font-sans">(x)</span>:</div>
              <div class="p-1.5 rounded bg-slate-950 text-slate-200 break-all my-1 select-all">${escapeHtml(ce.source_input)}</div>
              <div class="text-slate-400 mt-2">Output <span class="text-slate-500 font-sans">(f(x))</span>:</div>
              <div class="p-1.5 rounded bg-slate-950 text-emerald-400 break-all my-1 select-all">${escapeHtml(ce.source_output)}</div>
            </div>

            <!-- Follow-up Pair -->
            <div class="p-3 rounded bg-slate-900/80 border border-slate-800">
              <div class="text-cyan-400 font-bold mb-1">Follow-up Execution:</div>
              <div class="text-slate-400">Follow-up Input <span class="text-slate-500 font-sans">(x')</span>:</div>
              <div class="p-1.5 rounded bg-slate-950 text-slate-200 break-all my-1 select-all">${escapeHtml(ce.follow_up_input)}</div>
              <div class="text-slate-400 mt-2">Follow-up Output <span class="text-slate-500 font-sans">(f(x'))</span>:</div>
              <div class="p-1.5 rounded bg-slate-950 text-rose-400 break-all my-1 select-all">${escapeHtml(ce.follow_up_output)}</div>
            </div>
          </div>

          <div class="mt-3 p-2.5 rounded bg-rose-950/30 border border-rose-900/40 text-xs">
            <strong class="text-rose-300">Violation Reason:</strong>
            <span class="text-slate-300 ml-1 font-mono">${escapeHtml(ce.violation_message || 'Metamorphic relation assertion failed.')}</span>
          </div>
        </div>
      `;
    }).join('');
  }
}

/**
 * Mutation Testing Lab Controller
 */
async function runMutationLab() {
  const category = document.getElementById('mutation-category-select').value;
  const variant = document.getElementById('mutation-variant-select').value;
  const code = document.getElementById('studio-code-editor').value;
  const budget = parseInt(document.getElementById('mutation-budget-select').value, 10);
  const runBtn = document.getElementById('btn-run-mutation');

  runBtn.disabled = true;
  runBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⚙️</span> Synthesizing AST Mutants...`;

  try {
    const payload = {
      category: category,
      variant: variant,
      custom_code: category === 'Custom Python Code' ? code : null,
      test_budget: budget,
    };

    const res = await window.api.runMutation(payload);
    state.activeMutationRun = res;

    renderMutationResults(res);
    showToast(`Mutation testing completed! Mutation Score: ${res.mutation_score}%`, 'success');
  } catch (err) {
    showToast(`Mutation test failed: ${err.message}`, 'danger');
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `<span>🧬</span> Synthesize Mutants & Run Analysis`;
  }
}

function renderMutationResults(res) {
  document.getElementById('mutation-results-container').classList.remove('hidden');

  // Update Score Card
  document.getElementById('mutation-score-display').textContent = `${res.mutation_score}%`;
  document.getElementById('mutation-killed-count').textContent = res.killed_mutants;
  document.getElementById('mutation-survived-count').textContent = res.survived_mutants;
  document.getElementById('mutation-total-count').textContent = res.total_mutants;

  // Render Mutation Doughnut Chart
  renderMutationScoreChart('chart-mutation-score', res.killed_mutants, res.survived_mutants, res.error_mutants);

  // Render Mutants Table
  const tableBody = document.getElementById('mutation-table-body');
  tableBody.innerHTML = res.mutants.map(m => {
    const isKilled = m.status === 'KILLED';
    const statusBadge = isKilled
      ? `<span class="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">KILLED</span>`
      : `<span class="px-2 py-0.5 rounded text-xs font-bold bg-rose-950/60 text-rose-400 border border-rose-800/50">SURVIVED</span>`;

    return `
      <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 text-xs">
        <td class="py-3 px-4 font-mono font-bold text-slate-300">${m.mutant_id}</td>
        <td class="py-3 px-4">
          <span class="font-mono text-indigo-400">${m.operator}</span>
          <p class="text-[11px] text-slate-400 mt-0.5">${escapeHtml(m.description)}</p>
        </td>
        <td class="py-3 px-4 font-mono text-slate-400">Line ${m.line_number}</td>
        <td class="py-3 px-4">${statusBadge}</td>
        <td class="py-3 px-4 text-slate-300">${escapeHtml(m.killing_relation_name || 'None (Mutant survived test suite)')}</td>
        <td class="py-3 px-4">
          <button onclick="showMutantDiffModal('${m.mutant_id}')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px]">
            Inspect Diff
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function showMutantDiffModal(mutantId) {
  if (!state.activeMutationRun) return;
  const mutant = state.activeMutationRun.mutants.find(m => m.mutant_id === mutantId);
  if (!mutant) return;

  const modal = document.getElementById('modal-generic');
  const title = document.getElementById('modal-generic-title');
  const content = document.getElementById('modal-generic-content');

  title.textContent = `AST Mutant Diff: ${mutant.mutant_id} (${mutant.operator})`;
  content.innerHTML = `
    <div class="mb-3 text-xs text-slate-400">
      Operator: <strong class="text-indigo-400 font-mono">${mutant.operator}</strong> •
      Target Line: <strong class="text-slate-200 font-mono">${mutant.line_number}</strong> •
      Status: <strong class="${mutant.status === 'KILLED' ? 'text-emerald-400' : 'text-rose-400'}">${mutant.status}</strong>
    </div>
    <div class="p-3 rounded bg-slate-950 font-mono text-xs overflow-x-auto border border-slate-800">
      <pre class="text-slate-300 whitespace-pre">${escapeHtml(mutant.diff || 'No diff available')}</pre>
    </div>
    ${mutant.violation_message ? `
      <div class="mt-3 p-2.5 rounded bg-rose-950/30 border border-rose-900/40 text-xs">
        <strong class="text-rose-400">Killing Violation:</strong> ${escapeHtml(mutant.violation_message)}
      </div>
    ` : ''}
  `;

  modal.classList.remove('hidden');
}

/**
 * Phase 6 Empirical Benchmark Arena Controller
 */
async function runComparativeBenchmark() {
  const budget = parseInt(document.getElementById('benchmark-budget-select').value, 10);
  const runBtn = document.getElementById('btn-run-benchmark');

  runBtn.disabled = true;
  runBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⚙️</span> Running 3 Testing Paradigms across 7 Bugs...`;

  try {
    const res = await window.api.runBenchmark({ budget: budget });
    state.activeBenchmarkRun = res;

    renderBenchmarkResults(res);
    showToast('Phase 6 Benchmark completed successfully!', 'success');
  } catch (err) {
    showToast(`Benchmark run failed: ${err.message}`, 'danger');
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `<span>📊</span> Run Head-to-Head Benchmark`;
  }
}

function renderBenchmarkResults(res) {
  document.getElementById('benchmark-results-container').classList.remove('hidden');

  const results = res.results || [];
  const randomRes = results.find(r => r.technique_name.includes('Random')) || results[0];
  const unitRes = results.find(r => r.technique_name.includes('Unit')) || results[1];
  const metaRes = results.find(r => r.technique_name.includes('MetaOracle')) || results[2];

  // Head to Head Summary Cards
  document.getElementById('benchmark-random-rate').textContent = `${randomRes.detection_rate}%`;
  document.getElementById('benchmark-random-bugs').textContent = `${randomRes.detected_bugs_count}/${randomRes.total_evaluated_bugs}`;

  document.getElementById('benchmark-unit-rate').textContent = `${unitRes.detection_rate}%`;
  document.getElementById('benchmark-unit-bugs').textContent = `${unitRes.detected_bugs_count}/${unitRes.total_evaluated_bugs}`;

  document.getElementById('benchmark-meta-rate').textContent = `${metaRes.detection_rate}%`;
  document.getElementById('benchmark-meta-bugs').textContent = `${metaRes.detected_bugs_count}/${metaRes.total_evaluated_bugs}`;

  // Render Bar Chart
  renderBenchmarkChart('chart-benchmark-comparison', results);

  // Breakdown Table
  const tableBody = document.getElementById('benchmark-table-body');
  tableBody.innerHTML = results.map(r => `
    <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 text-xs">
      <td class="py-3 px-4 font-bold text-slate-200">${escapeHtml(r.technique_name)}</td>
      <td class="py-3 px-4 font-mono text-slate-300">${escapeHtml(r.oracle_type)}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[11px] font-bold ${r.oracle_effort === 'Zero' ? 'bg-slate-800 text-slate-300' : r.oracle_effort === 'High' ? 'bg-rose-950/60 text-rose-400' : 'bg-emerald-950/60 text-emerald-400'}">${escapeHtml(r.oracle_effort)}</span>
      </td>
      <td class="py-3 px-4 font-mono font-bold text-indigo-400">${r.detection_rate}%</td>
      <td class="py-3 px-4 font-mono text-slate-300">${r.detected_bugs_count} / ${r.total_evaluated_bugs}</td>
      <td class="py-3 px-4 text-slate-400">${escapeHtml(r.notes)}</td>
    </tr>
  `).join('');
}

/**
 * Relations Catalog Controller
 */
function renderRelationsCatalog(relations) {
  const container = document.getElementById('relations-catalog-grid');
  if (!container) return;

  container.innerHTML = relations.map(r => `
    <div class="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition glass-panel-hover flex flex-col justify-between">
      <div>
        <div class="flex items-start justify-between">
          <span class="px-2.5 py-0.5 rounded bg-slate-800 text-[11px] font-mono font-bold text-indigo-400 uppercase">${escapeHtml(r.category)}</span>
          <span class="text-xs font-mono text-slate-500">${r.is_custom ? 'CUSTOM' : 'BUILT-IN'}</span>
        </div>
        <h3 class="text-base font-bold text-slate-100 mt-2">${escapeHtml(r.name)}</h3>
        <p class="text-xs text-slate-400 mt-1 line-clamp-2">${escapeHtml(r.description)}</p>
        
        <div class="mt-3 p-2.5 rounded bg-slate-950 border border-slate-800/80">
          <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Formal Invariant Formula:</div>
          <div class="text-xs font-mono text-cyan-400 font-semibold mt-0.5 break-all">${escapeHtml(r.formula || 'R(x, x\', f(x), f(x\')) == True')}</div>
        </div>
      </div>
      
      <div class="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <span class="font-mono text-[11px] text-slate-500">${escapeHtml(r.relation_id)}</span>
        <button onclick="copyToClipboard('${escapeHtml(r.formula || '')}')" class="text-indigo-400 hover:text-indigo-300">Copy Formula</button>
      </div>
    </div>
  `).join('');
}

function filterRelationsCatalog() {
  const search = document.getElementById('relations-search-input').value.toLowerCase();
  const category = document.getElementById('relations-category-filter').value;

  const filtered = state.relations.filter(r => {
    const matchesSearch = r.name.toLowerCase().includes(search) ||
                          r.description.toLowerCase().includes(search) ||
                          r.relation_id.toLowerCase().includes(search);
    const matchesCategory = category === 'ALL' || r.category.toUpperCase() === category.toUpperCase();
    return matchesSearch && matchesCategory;
  });

  renderRelationsCatalog(filtered);
}

/**
 * Add Custom Relation Modal
 */
function openAddRelationModal() {
  document.getElementById('modal-add-relation').classList.remove('hidden');
}

async function submitCustomRelation(event) {
  event.preventDefault();
  const id = document.getElementById('custom-rel-id').value.trim();
  const name = document.getElementById('custom-rel-name').value.trim();
  const category = document.getElementById('custom-rel-category').value.trim();
  const formula = document.getElementById('custom-rel-formula').value.trim();
  const description = document.getElementById('custom-rel-description').value.trim();

  try {
    const res = await window.api.addCustomRelation({
      relation_id: id,
      name: name,
      category: category,
      formula: formula,
      description: description,
    });

    state.relations = await window.api.getRelations();
    renderRelationsCatalog(state.relations);
    populateRelationsChecklist();

    document.getElementById('modal-add-relation').classList.add('hidden');
    showToast(`Custom relation "${name}" registered successfully!`, 'success');
  } catch (err) {
    showToast(`Failed to add relation: ${err.message}`, 'danger');
  }
}

/**
 * Test Run History Controller
 */
async function loadHistory() {
  try {
    const history = await window.api.getTestHistory();
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;

    if (history.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-8 text-slate-400 text-xs">No test runs recorded in database yet. Run a test suite to view history.</td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = history.map(r => {
      const isViolated = r.status === 'VIOLATED';
      const statusBadge = isViolated
        ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950/60 text-amber-400 border border-amber-800/50">VIOLATIONS</span>`
        : `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">PASSED</span>`;

      const dateStr = r.created_at ? new Date(r.created_at).toLocaleString() : 'N/A';

      return `
        <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 text-xs">
          <td class="py-3 px-4 font-mono font-bold text-slate-300">#${r.id}</td>
          <td class="py-3 px-4 text-slate-400">${dateStr}</td>
          <td class="py-3 px-4 font-mono text-indigo-300">${escapeHtml(r.function_name)}</td>
          <td class="py-3 px-4 text-slate-300">${escapeHtml(r.category)}</td>
          <td class="py-3 px-4 font-mono font-bold ${isViolated ? 'text-amber-400' : 'text-emerald-400'}">${r.pass_rate}%</td>
          <td class="py-3 px-4 font-mono text-slate-300">${r.total_tests} (${r.counterexamples_count} bugs)</td>
          <td class="py-3 px-4">${statusBadge}</td>
          <td class="py-3 px-4 flex items-center space-x-2">
            <button onclick="inspectPastRun(${r.id})" class="px-2 py-1 rounded bg-indigo-950/60 hover:bg-indigo-900 text-indigo-300 border border-indigo-800/50 text-[11px]">Inspect</button>
            <button onclick="exportRunJson(${r.id})" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px]">JSON</button>
            <button onclick="deleteRunRecord(${r.id})" class="px-2 py-1 rounded bg-rose-950/40 hover:bg-rose-900 text-rose-400 border border-rose-800/40 text-[11px]">Delete</button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('History load error:', err);
  }
}

async function inspectPastRun(runId) {
  try {
    const report = await window.api.getTestRun(runId);
    state.activeTestRun = report;
    switchTab('studio');
    renderStudioResults(report);
    showToast(`Loaded details for Run #${runId}`, 'success');
  } catch (err) {
    showToast(`Failed to load run: ${err.message}`, 'danger');
  }
}

async function exportRunJson(runId) {
  try {
    const report = await window.api.getTestRun(runId);
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `metaoracle_run_${runId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  } catch (err) {
    showToast(`Export failed: ${err.message}`, 'danger');
  }
}

async function deleteRunRecord(runId) {
  if (!confirm(`Are you sure you want to delete Test Run #${runId}?`)) return;
  try {
    await window.api.deleteTestRun(runId);
    showToast(`Run #${runId} deleted.`, 'success');
    await loadHistory();
    await refreshDashboard();
  } catch (err) {
    showToast(`Deletion failed: ${err.message}`, 'danger');
  }
}

/**
 * Snippets Controller
 */
async function loadSnippets() {
  try {
    state.snippets = await window.api.getSnippets();
    const container = document.getElementById('snippets-list-container');
    if (!container) return;

    if (state.snippets.length === 0) {
      container.innerHTML = `
        <div class="col-span-full p-6 text-center text-slate-400 border border-dashed border-slate-800 rounded-xl text-xs">
          No saved snippets yet. Write an algorithm and save it to test repeatedly.
        </div>
      `;
      return;
    }

    container.innerHTML = state.snippets.map(s => `
      <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold text-slate-100">${escapeHtml(s.title)}</span>
            <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400">${escapeHtml(s.category)}</span>
          </div>
          <div class="mt-2 p-2 rounded bg-slate-950 font-mono text-[11px] text-slate-300 max-h-24 overflow-y-auto">
            <pre class="whitespace-pre">${escapeHtml(s.code)}</pre>
          </div>
        </div>
        <div class="mt-3 pt-2 border-t border-slate-800/60 flex justify-between">
          <button onclick="loadSnippetIntoStudio(${s.id})" class="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">Load into Studio</button>
          <button onclick="deleteSnippetRecord(${s.id})" class="text-xs text-rose-400 hover:text-rose-300">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load snippets:', err);
  }
}

function loadSnippetIntoStudio(snippetId) {
  const snippet = state.snippets.find(s => s.id === snippetId);
  if (!snippet) return;

  switchTab('studio');
  document.getElementById('studio-category-select').value = 'Custom Python Code';
  updateVariantOptions();
  document.getElementById('studio-code-editor').value = snippet.code;
  document.getElementById('studio-input-type').value = snippet.input_type || 'list';
  showToast(`Loaded snippet "${snippet.title}" into Studio.`, 'success');
}

async function saveCurrentSnippet() {
  const title = prompt('Enter a title for this snippet:');
  if (!title) return;

  const code = document.getElementById('studio-code-editor').value;
  const category = document.getElementById('studio-category-select').value;
  const inputType = document.getElementById('studio-input-type').value;

  try {
    await window.api.createSnippet({
      title: title,
      code: code,
      category: category,
      input_type: inputType,
    });
    showToast(`Snippet "${title}" saved!`, 'success');
    await loadSnippets();
  } catch (err) {
    showToast(`Failed to save snippet: ${err.message}`, 'danger');
  }
}

async function deleteSnippetRecord(snippetId) {
  if (!confirm('Delete this saved snippet?')) return;
  try {
    await window.api.deleteSnippet(snippetId);
    showToast('Snippet deleted.', 'success');
    await loadSnippets();
  } catch (err) {
    showToast(`Failed to delete snippet: ${err.message}`, 'danger');
  }
}

/**
 * Dashboard Refresh
 */
async function refreshDashboard() {
  try {
    const stats = await window.api.getDashboardStats();
    
    document.getElementById('stat-total-runs').textContent = stats.total_runs;
    document.getElementById('stat-total-tests').textContent = stats.total_tests_executed;
    document.getElementById('stat-total-violations').textContent = stats.total_violations_detected;
    document.getElementById('stat-pass-rate').textContent = `${stats.overall_pass_rate}%`;

    // Render Trend Chart
    renderTrendChart('chart-dashboard-trend', stats.recent_runs);

    // Recent Feed Table
    const feedBody = document.getElementById('dashboard-recent-table');
    if (feedBody) {
      if (stats.recent_runs.length === 0) {
        feedBody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-400 text-xs">No recent test runs. Execute tests in Studio to populate.</td></tr>`;
      } else {
        feedBody.innerHTML = stats.recent_runs.map(r => `
          <tr class="border-b border-slate-800/40 text-xs">
            <td class="py-2.5 px-3 font-mono font-bold text-slate-300">#${r.id}</td>
            <td class="py-2.5 px-3 font-mono text-indigo-300">${escapeHtml(r.function_name)}</td>
            <td class="py-2.5 px-3 font-mono font-semibold ${r.pass_rate < 100 ? 'text-amber-400' : 'text-emerald-400'}">${r.pass_rate}%</td>
            <td class="py-2.5 px-3">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'VIOLATED' ? 'bg-amber-950/60 text-amber-400' : 'bg-emerald-950/60 text-emerald-400'}">${r.status}</span>
            </td>
            <td class="py-2.5 px-3">
              <button onclick="inspectPastRun(${r.id})" class="text-indigo-400 hover:text-indigo-300 text-xs">Inspect</button>
            </td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load dashboard metrics:', err);
  }
}

/**
 * Event Listeners Initializer
 */
function initEventListeners() {
  // Category dropdown change
  const catSelect = document.getElementById('studio-category-select');
  if (catSelect) {
    catSelect.addEventListener('change', updateVariantOptions);
  }

  // Variant dropdown change
  const varSelect = document.getElementById('studio-variant-select');
  if (varSelect) {
    varSelect.addEventListener('change', onPresetSelectionChange);
  }

  // Auto-suggest button
  const suggestBtn = document.getElementById('btn-auto-suggest');
  if (suggestBtn) {
    suggestBtn.addEventListener('click', triggerAutoSuggest);
  }

  // Run tests button
  const runTestsBtn = document.getElementById('btn-run-tests');
  if (runTestsBtn) {
    runTestsBtn.addEventListener('click', runMetamorphicStudioTests);
  }

  // Budget slider
  const slider = document.getElementById('studio-budget-slider');
  const sliderVal = document.getElementById('studio-budget-value');
  if (slider && sliderVal) {
    slider.addEventListener('input', (e) => {
      sliderVal.textContent = e.target.value;
    });
  }

  // Mutation Category change
  const mutCat = document.getElementById('mutation-category-select');
  if (mutCat) {
    mutCat.addEventListener('change', () => {
      const variantSel = document.getElementById('mutation-variant-select');
      const cat = mutCat.value;
      const presets = state.presets.filter(p => p.category === cat);
      variantSel.innerHTML = presets.map(p => `<option value="${p.variant}">${p.variant}</option>`).join('');
    });
  }

  // Run mutation button
  const runMutationBtn = document.getElementById('btn-run-mutation');
  if (runMutationBtn) {
    runMutationBtn.addEventListener('click', runMutationLab);
  }

  // Run benchmark button
  const runBenchmarkBtn = document.getElementById('btn-run-benchmark');
  if (runBenchmarkBtn) {
    runBenchmarkBtn.addEventListener('click', runComparativeBenchmark);
  }

  // Relations filter
  const searchInput = document.getElementById('relations-search-input');
  if (searchInput) searchInput.addEventListener('input', filterRelationsCatalog);

  const catFilter = document.getElementById('relations-category-filter');
  if (catFilter) catFilter.addEventListener('change', filterRelationsCatalog);

  // Custom relation form
  const customRelForm = document.getElementById('form-custom-relation');
  if (customRelForm) customRelForm.addEventListener('submit', submitCustomRelation);

  // Close modals
  document.querySelectorAll('.btn-close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
    });
  });
}

/**
 * Toast Notifications Utility
 */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const bgColors = {
    success: 'bg-emerald-950/90 border-emerald-600 text-emerald-200',
    danger: 'bg-rose-950/90 border-rose-600 text-rose-200',
    warning: 'bg-amber-950/90 border-amber-600 text-amber-200',
    info: 'bg-indigo-950/90 border-indigo-600 text-indigo-200',
  };

  const toast = document.createElement('div');
  toast.className = `p-3.5 rounded-lg border shadow-xl flex items-center justify-between text-xs backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0 ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button class="ml-3 text-slate-400 hover:text-white" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'info');
  });
}
