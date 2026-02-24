/* ============================================
   ML Training Monitor — API Client & Utilities
   Shared across all pages
   ============================================ */

const API_BASE = 'http://localhost:8000';

const api = {
  // ── Models ──────────────────────────────
  async getModels() {
    const res = await fetch(`${API_BASE}/models/`);
    if (!res.ok) throw new Error(`Failed to fetch models: ${res.status}`);
    return res.json();
  },

  async deleteModel(modelId) {
    const res = await fetch(`${API_BASE}/models/${modelId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete model: ${res.status}`);
    return res.json();
  },

  // ── Runs ────────────────────────────────
  async getRunsByModel(modelId) {
    const res = await fetch(`${API_BASE}/runs/runbymodels/${modelId}`);
    if (res.status === 404) return [];
    if (!res.ok) throw new Error(`Failed to fetch runs: ${res.status}`);
    return res.json();
  },

  async updateHyperparameters(runId, hyperparameters) {
    const res = await fetch(`${API_BASE}/runs/update_hyperparam`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId, new_hyperpamar: hyperparameters }),
    });
    if (!res.ok) throw new Error(`Failed to update hyperparameters: ${res.status}`);
    return res.json();
  },

  async deleteRun(runId) {
    const res = await fetch(`${API_BASE}/runs/${runId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete run: ${res.status}`);
    return res.json();
  },

  async updateNote(runId, newNote) {
    const res = await fetch(`${API_BASE}/runs/update_note`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId, new_note: newNote }),
    });
    if (!res.ok) throw new Error(`Failed to update note: ${res.status}`);
    return res.json();
  },

  // ── Losses ──────────────────────────────
  async getLosses(runId, split = null) {
    let url = `${API_BASE}/loss/?run_id=${runId}`;
    if (split) url += `&split=${split}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch losses: ${res.status}`);
    return res.json();
  },

  // ── Metrics ─────────────────────────────
  async getMetrics(runId, split = null, metricName = null) {
    let url = `${API_BASE}/metric/?run_id=${runId}`;
    if (split) url += `&split=${split}`;
    if (metricName) url += `&metric_name=${encodeURIComponent(metricName)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
    return res.json();
  },
};

// ── Utility Functions ───────────────────────

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function formatDate(dateString) {
  if (!dateString) return '—';
  const d = new Date(dateString);
  return d.toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function shortId(uuid) {
  return uuid ? uuid.substring(0, 8) : '';
}

function getStatusClass(status) {
  return status || 'running';
}

// ── Theme Manager ───────────────────────────

const ThemeManager = {
  STORAGE_KEY: 'ml-monitor-theme',

  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY) || 'dark';
    this.set(saved);
  },

  get() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  },

  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.STORAGE_KEY, theme);
    this.updateToggleIcon();
  },

  toggle() {
    this.set(this.get() === 'dark' ? 'light' : 'dark');
  },

  updateToggleIcon() {
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = this.get() === 'dark' ? '☀️' : '🌙';
  },

  /** Returns chart text colors based on current theme */
  chartColors() {
    const isDark = this.get() === 'dark';
    return {
      text: isDark ? '#999' : '#666',
      textLight: isDark ? '#666' : '#999',
      grid: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)',
      tooltipBg: isDark ? 'rgba(26,26,26,0.95)' : 'rgba(255,255,255,0.95)',
      tooltipTitle: isDark ? '#e8e8e8' : '#1a1a1a',
      tooltipBody: isDark ? '#999' : '#666',
      tooltipBorder: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
    };
  },
};

// Initialize theme immediately
ThemeManager.init();

// ── SVG Icons ───────────────────────────────

const icons = {
  brain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A5.5 5.5 0 0 0 4 7.5c0 1.58.7 3 1.81 3.98L4 14l2.5 1 1 3h5l1-3 2.5-1-1.81-2.52A5.5 5.5 0 0 0 9.5 2z"/><path d="M14.5 2A5.5 5.5 0 0 1 20 7.5c0 1.58-.7 3-1.81 3.98"/></svg>`,
  experiment: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6M12 3v7l5.5 8.5a1 1 0 0 1-.9 1.5H7.4a1 1 0 0 1-.9-1.5L12 10V3z"/></svg>`,
  pencil: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  layers: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84Z"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/></svg>`,
  arrowLeft: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>`,
  compare: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>`,
  home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  folder: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>`,
  activity: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`,
  note: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
};

// ── Fullscreen Chart ────────────────────────

function openFullscreenChart(chartCreateFn) {
  const overlay = document.createElement('div');
  overlay.className = 'chart-fullscreen-overlay';
  overlay.innerHTML = `
    <div class="chart-fullscreen-inner">
      <button class="chart-fullscreen-close" title="Close">✕</button>
      <canvas id="fullscreen-canvas"></canvas>
    </div>`;
  document.body.appendChild(overlay);

  const canvas = overlay.querySelector('#fullscreen-canvas');
  const chart = chartCreateFn(canvas);

  const close = () => { chart.destroy(); overlay.remove(); };
  overlay.querySelector('.chart-fullscreen-close').addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', handler); }
  });
}

// ── Polling Manager ─────────────────────────

class PollingManager {
  constructor(intervalMs = 3000) {
    this.intervalMs = intervalMs;
    this.timers = [];
  }

  start(callback) {
    callback();
    const id = setInterval(callback, this.intervalMs);
    this.timers.push(id);
    return id;
  }

  stop(id) {
    clearInterval(id);
    this.timers = this.timers.filter(t => t !== id);
  }

  stopAll() {
    this.timers.forEach(id => clearInterval(id));
    this.timers = [];
  }
}

// ── Hyperparameter Edit Modal ───────────────

function openHyperparamModal(runId, hyperparameters, onSave) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay visible';

  const params = hyperparameters ? { ...hyperparameters } : {};

  function renderParams() {
    return Object.entries(params).map(([key, value]) => `
      <div class="param-row" data-key="${key}">
        <input class="param-input param-key" value="${key}" placeholder="Key" />
        <input class="param-input param-value" value="${value}" placeholder="Value" />
        <button class="param-delete" title="Remove">−</button>
      </div>
    `).join('');
  }

  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3 class="modal-title">Edit Hyperparameters</h3>
        <button class="modal-close" id="modal-close">✕</button>
      </div>
      <div id="params-container">${renderParams()}</div>
      <button class="add-param-btn" id="add-param"><span>+</span> Add Parameter</button>
      <div class="modal-footer">
        <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
        <button class="btn btn-primary" id="modal-save">Save Changes</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  const close = () => {
    overlay.classList.remove('visible');
    setTimeout(() => overlay.remove(), 300);
  };

  overlay.querySelector('#modal-close').addEventListener('click', close);
  overlay.querySelector('#modal-cancel').addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });

  overlay.querySelector('#add-param').addEventListener('click', () => {
    const container = overlay.querySelector('#params-container');
    const row = document.createElement('div');
    row.className = 'param-row';
    row.innerHTML = `
      <input class="param-input param-key" value="" placeholder="Key" />
      <input class="param-input param-value" value="" placeholder="Value" />
      <button class="param-delete" title="Remove">−</button>
    `;
    container.appendChild(row);
    row.querySelector('.param-key').focus();
  });

  overlay.querySelector('#params-container').addEventListener('click', (e) => {
    if (e.target.classList.contains('param-delete')) e.target.closest('.param-row').remove();
  });

  overlay.querySelector('#modal-save').addEventListener('click', async () => {
    const rows = overlay.querySelectorAll('.param-row');
    const newParams = {};
    rows.forEach(row => {
      const key = row.querySelector('.param-key').value.trim();
      const val = row.querySelector('.param-value').value.trim();
      if (key) {
        const num = Number(val);
        newParams[key] = isNaN(num) || val === '' ? val : num;
      }
    });

    try {
      await onSave(runId, newParams);
      close();
    } catch (err) {
      alert('Failed to save hyperparameters. The API endpoint may not be available yet.');
      console.error(err);
    }
  });
}

// ── Confirm Modal ───────────────────────────

function openConfirmModal(title, message, onConfirm) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay visible';

  overlay.innerHTML = `
    <div class="modal confirm-modal">
      <div class="modal-header">
        <h3 class="modal-title">${title}</h3>
        <button class="modal-close" id="confirm-close">✕</button>
      </div>
      <div class="confirm-modal-body">
        <p>${message}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" id="confirm-cancel">Cancel</button>
        <button class="btn btn-danger" id="confirm-ok">Delete</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  const close = () => {
    overlay.classList.remove('visible');
    setTimeout(() => overlay.remove(), 300);
  };

  overlay.querySelector('#confirm-close').addEventListener('click', close);
  overlay.querySelector('#confirm-cancel').addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  overlay.querySelector('#confirm-ok').addEventListener('click', async () => {
    try {
      await onConfirm();
      close();
    } catch (err) {
      alert('Operation failed: ' + err.message);
      console.error(err);
    }
  });
}

// ── Navbar Builder (shared across pages) ────

function buildNavbar(activePage) {
  return `
    <nav class="navbar">
      <a href="index.html" class="navbar-brand">
        ${icons.chart}
        ML Monitor
      </a>
      <div class="navbar-right">
        <div class="navbar-links">
          <a href="index.html" class="${activePage === 'home' ? 'active' : ''}">Dashboard</a>
        </div>
        <button class="theme-toggle" id="theme-toggle" onclick="ThemeManager.toggle()" title="Toggle theme">
          ${ThemeManager.get() === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </nav>`;
}
