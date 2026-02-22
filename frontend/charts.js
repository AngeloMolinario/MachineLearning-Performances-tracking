/* ============================================
   ML Training Monitor — Chart Helpers
   Chart.js wrappers with min/max annotations
   ============================================ */

// Color palette for multi-run comparison
const RUN_COLORS = [
    { bg: 'rgba(150,150,150,0.12)', border: '#b0b0b0' },
    { bg: 'rgba(91,192,222,0.12)', border: '#5bc0de' },
    { bg: 'rgba(245,166,35,0.12)', border: '#f5a623' },
    { bg: 'rgba(92,184,92,0.12)', border: '#5cb85c' },
    { bg: 'rgba(217,83,79,0.12)', border: '#d9534f' },
    { bg: 'rgba(155,89,182,0.12)', border: '#9b59b6' },
    { bg: 'rgba(243,156,18,0.12)', border: '#f39c12' },
    { bg: 'rgba(52,152,219,0.12)', border: '#3498db' },
];

const SPLIT_COLORS = {
    train: { bg: 'rgba(180,180,180,0.12)', border: '#b0b0b0' },
    validation: { bg: 'rgba(245,166,35,0.12)', border: '#f5a623' },
};

const MIN_COLOR = '#d9534f';  // Red for minimum
const MAX_COLOR = '#5cb85c';  // Green for maximum

// ── Common Chart.js config ──────────────────

function getChartDefaults() {
    const tc = ThemeManager.chartColors();
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: {
                labels: {
                    color: tc.text,
                    font: { family: 'Inter', size: 14, weight: '500' },
                    usePointStyle: true,
                    pointStyleWidth: 12,
                    padding: 20,
                },
            },
            tooltip: {
                backgroundColor: tc.tooltipBg,
                titleColor: tc.tooltipTitle,
                bodyColor: tc.tooltipBody,
                borderColor: tc.tooltipBorder,
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
                titleFont: { family: 'Inter', weight: '600' },
                bodyFont: { family: 'Inter' },
            },
        },
        scales: {
            x: {
                type: 'linear',
                title: { display: true, text: 'Step', color: tc.textLight, font: { family: 'Inter', size: 12 } },
                ticks: { color: tc.textLight, font: { family: 'Inter', size: 11 }, precision: 0 },
                grid: { color: tc.grid },
            },
            y: {
                title: { display: true, text: 'Value', color: tc.textLight, font: { family: 'Inter', size: 12 } },
                ticks: { color: tc.textLight, font: { family: 'Inter', size: 11 } },
                grid: { color: tc.grid },
            },
        },
    };
}

// ── Min/Max Helpers ─────────────────────────

/**
 * Find min/max points in a dataset array of {x, y} objects.
 * Returns { min: {x, y}, max: {x, y} } or null if empty.
 */
function findMinMax(dataPoints) {
    if (!dataPoints || dataPoints.length === 0) return null;
    let min = dataPoints[0], max = dataPoints[0];
    for (const p of dataPoints) {
        if (p.y < min.y) min = p;
        if (p.y > max.y) max = p;
    }
    return { min, max };
}

/**
 * Create annotation datasets for min/max points.
 * @param {Array} datasets - existing datasets
 * @param {boolean} showMin
 * @param {boolean} showMax
 * @returns {Array} extra datasets to add
 */
function createMinMaxDatasets(datasets, showMin, showMax) {
    const extras = [];

    datasets.forEach(ds => {
        const mm = findMinMax(ds.data);
        if (!mm) return;

        if (showMin) {
            extras.push({
                label: `Min (${ds.label}): ${mm.min.y.toFixed(4)} @ step ${mm.min.x}`,
                data: [{ x: mm.min.x, y: mm.min.y }],
                borderColor: MIN_COLOR,
                backgroundColor: MIN_COLOR,
                pointRadius: 7,
                pointHoverRadius: 9,
                pointStyle: 'circle',
                showLine: false,
                borderWidth: 2,
            });
        }

        if (showMax) {
            extras.push({
                label: `Max (${ds.label}): ${mm.max.y.toFixed(4)} @ step ${mm.max.x}`,
                data: [{ x: mm.max.x, y: mm.max.y }],
                borderColor: MAX_COLOR,
                backgroundColor: MAX_COLOR,
                pointRadius: 7,
                pointHoverRadius: 9,
                pointStyle: 'triangle',
                showLine: false,
                borderWidth: 2,
            });
        }
    });

    return extras;
}

// ── Data Parsers ────────────────────────────

function splitData(data) {
    const result = { train: { steps: [], values: [] }, validation: { steps: [], values: [] } };
    const sorted = [...data].sort((a, b) => a.step - b.step);
    sorted.forEach(d => {
        if (result[d.split]) {
            result[d.split].steps.push(d.step);
            result[d.split].values.push(d.value);
        }
    });
    return result;
}

// ── Single-Run: Overlay Chart ───────────────

function createOverlayChart(canvas, data, title, existingChart, showMin = false, showMax = false) {
    const split = splitData(data);

    const coreDatasets = [];
    if (split.train.values.length > 0) {
        coreDatasets.push({
            label: 'Train',
            data: split.train.steps.map((s, i) => ({ x: s, y: split.train.values[i] })),
            borderColor: SPLIT_COLORS.train.border,
            backgroundColor: SPLIT_COLORS.train.bg,
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
        });
    }
    if (split.validation.values.length > 0) {
        coreDatasets.push({
            label: 'Validation',
            data: split.validation.steps.map((s, i) => ({ x: s, y: split.validation.values[i] })),
            borderColor: SPLIT_COLORS.validation.border,
            backgroundColor: SPLIT_COLORS.validation.bg,
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
        });
    }

    const datasets = [...coreDatasets, ...createMinMaxDatasets(coreDatasets, showMin, showMax)];

    if (existingChart) {
        existingChart.data.datasets = datasets;
        existingChart.options.plugins.title = chartTitle(title);
        existingChart.update('none');
        return existingChart;
    }

    const opts = getChartDefaults();
    opts.plugins.title = chartTitle(title);
    return new Chart(canvas, { type: 'line', data: { datasets }, options: opts });
}

// ── Single-Run: Split Chart ─────────────────

function createSingleSplitChart(canvas, data, splitName, title, existingChart, showMin = false, showMax = false) {
    const sorted = [...data].filter(d => d.split === splitName).sort((a, b) => a.step - b.step);
    const color = SPLIT_COLORS[splitName] || SPLIT_COLORS.train;

    const coreDatasets = [{
        label: splitName.charAt(0).toUpperCase() + splitName.slice(1),
        data: sorted.map(d => ({ x: d.step, y: d.value })),
        borderColor: color.border, backgroundColor: color.bg,
        borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
    }];

    const datasets = [...coreDatasets, ...createMinMaxDatasets(coreDatasets, showMin, showMax)];

    if (existingChart) {
        existingChart.data.datasets = datasets;
        existingChart.options.plugins.title = chartTitle(title);
        existingChart.update('none');
        return existingChart;
    }

    const opts = getChartDefaults();
    opts.plugins.title = chartTitle(title);
    return new Chart(canvas, { type: 'line', data: { datasets }, options: opts });
}

// ── Multi-Run: Comparison Chart ─────────────

function createComparisonChart(canvas, runsData, splitFilter, title, existingChart, showMin = false, showMax = false) {
    const coreDatasets = [];
    let colorIdx = 0;

    Object.entries(runsData).forEach(([runId, { data, label }]) => {
        const splits = splitFilter ? [splitFilter] : ['train', 'validation'];
        splits.forEach(sp => {
            const filtered = data.filter(d => d.split === sp).sort((a, b) => a.step - b.step);
            if (filtered.length === 0) return;
            const color = RUN_COLORS[colorIdx % RUN_COLORS.length];
            coreDatasets.push({
                label: `${label} (${sp})`,
                data: filtered.map(d => ({ x: d.step, y: d.value })),
                borderColor: color.border, backgroundColor: color.bg,
                borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: false,
            });
            colorIdx++;
        });
    });

    const datasets = [...coreDatasets, ...createMinMaxDatasets(coreDatasets, showMin, showMax)];

    if (existingChart) {
        existingChart.data.datasets = datasets;
        existingChart.options.plugins.title = chartTitle(title);
        existingChart.update('none');
        return existingChart;
    }

    const opts = getChartDefaults();
    opts.plugins.title = chartTitle(title);
    return new Chart(canvas, { type: 'line', data: { datasets }, options: opts });
}

// ── Utility ─────────────────────────────────

function chartTitle(text) {
    const tc = ThemeManager.chartColors();
    return { display: true, text, color: tc.tooltipTitle, font: { family: 'Inter', size: 14, weight: '600' } };
}
