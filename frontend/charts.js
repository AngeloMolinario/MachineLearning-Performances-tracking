/* ============================================
   ML Training Monitor — Chart Helpers
   Chart.js wrappers with multitask + min/max
   ============================================ */

const RUN_COLORS = [
    { bg: 'rgba(0,123,255,0.12)', border: '#007bff' }, // Blue
    { bg: 'rgba(220,53,69,0.12)', border: '#dc3545' }, // Red
    { bg: 'rgba(40,167,69,0.12)', border: '#28a745' }, // Green
    { bg: 'rgba(111,66,193,0.12)', border: '#6f42c1' }, // Purple
    { bg: 'rgba(253,126,20,0.12)', border: '#fd7e14' }, // Orange
    { bg: 'rgba(23,162,184,0.12)', border: '#17a2b8' }, // Cyan
    { bg: 'rgba(232,62,140,0.12)', border: '#e83e8c' }, // Pink
    { bg: 'rgba(255,193,7,0.12)', border: '#ffc107' }, // Yellow
];

// Task colors (distinct palette for multitask)
const TASK_COLORS = [
    { bg: 'rgba(0,123,255,0.12)', border: '#007bff' }, // Blue
    { bg: 'rgba(220,53,69,0.12)', border: '#dc3545' }, // Red
    { bg: 'rgba(40,167,69,0.12)', border: '#28a745' }, // Green
    { bg: 'rgba(111,66,193,0.12)', border: '#6f42c1' }, // Purple
    { bg: 'rgba(253,126,20,0.12)', border: '#fd7e14' }, // Orange
    { bg: 'rgba(23,162,184,0.12)', border: '#17a2b8' }, // Cyan
    { bg: 'rgba(232,62,140,0.12)', border: '#e83e8c' }, // Pink
    { bg: 'rgba(255,193,7,0.12)', border: '#ffc107' }, // Yellow
];

const SPLIT_COLORS = {
    train: { bg: 'rgba(180,180,180,0.12)', border: '#b0b0b0' },
    validation: { bg: 'rgba(245,166,35,0.12)', border: '#f5a623' },
};

const MIN_COLOR = '#d9534f';
const MAX_COLOR = '#5cb85c';

const SINGLE_TASK = '__single_task__';

// ── Multitask helpers ───────────────────────

/**
 * Extract unique task names from a loss/metric array.
 * Returns sorted list; __single_task__ first if present.
 */
function extractTaskNames(data) {
    const tasks = [...new Set(data.map(d => d.task_name || SINGLE_TASK))];
    tasks.sort((a, b) => {
        if (a === SINGLE_TASK) return -1;
        if (b === SINGLE_TASK) return 1;
        return a.localeCompare(b);
    });
    return tasks;
}

/**
 * Human-readable label for a task name.
 */
function taskLabel(taskName) {
    return taskName === SINGLE_TASK ? 'All' : taskName;
}

/**
 * Filter data by task name.
 */
function filterByTask(data, taskName) {
    return data.filter(d => (d.task_name || SINGLE_TASK) === taskName);
}

/**
 * Check if a dataset is truly multitask (has >1 distinct task OR single non-default task).
 */
function isMultitask(data) {
    const tasks = extractTaskNames(data);
    return tasks.length > 1 || (tasks.length === 1 && tasks[0] !== SINGLE_TASK);
}

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
                position: 'bottom',
                align: 'center',
                labels: {
                    color: tc.text,
                    font: { family: 'Inter', size: 13, weight: '500' },
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

// ── Min/Max ─────────────────────────────────

function findMinMax(dataPoints) {
    if (!dataPoints || dataPoints.length === 0) return null;
    let min = dataPoints[0], max = dataPoints[0];
    for (const p of dataPoints) {
        if (p.y < min.y) min = p;
        if (p.y > max.y) max = p;
    }
    return { min, max };
}

function createMinMaxDatasets(datasets, showMin, showMax) {
    const extras = [];
    datasets.forEach(ds => {
        const mm = findMinMax(ds.data);
        if (!mm) return;
        if (showMin) {
            extras.push({
                label: `Min (${ds.label}): ${mm.min.y.toFixed(4)} @ step ${mm.min.x}`,
                data: [{ x: mm.min.x, y: mm.min.y }],
                borderColor: MIN_COLOR, backgroundColor: MIN_COLOR,
                pointRadius: 7, pointHoverRadius: 9, pointStyle: 'circle',
                showLine: false, borderWidth: 2,
            });
        }
        if (showMax) {
            extras.push({
                label: `Max (${ds.label}): ${mm.max.y.toFixed(4)} @ step ${mm.max.x}`,
                data: [{ x: mm.max.x, y: mm.max.y }],
                borderColor: MAX_COLOR, backgroundColor: MAX_COLOR,
                pointRadius: 7, pointHoverRadius: 9, pointStyle: 'triangle',
                showLine: false, borderWidth: 2,
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

// ── Single-Run: Overlay Chart (single task) ─

function createOverlayChart(canvas, data, title, existingChart, showMin = false, showMax = false) {
    const split = splitData(data);
    const coreDatasets = [];
    if (split.train.values.length > 0) {
        coreDatasets.push({
            label: 'Train [Solid]',
            data: split.train.steps.map((s, i) => ({ x: s, y: split.train.values[i] })),
            borderColor: SPLIT_COLORS.train.border, backgroundColor: SPLIT_COLORS.train.bg,
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
            borderDash: [],
        });
    }
    if (split.validation.values.length > 0) {
        coreDatasets.push({
            label: 'Validation [Dashed]',
            data: split.validation.steps.map((s, i) => ({ x: s, y: split.validation.values[i] })),
            borderColor: SPLIT_COLORS.validation.border, backgroundColor: SPLIT_COLORS.validation.bg,
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
            borderDash: [5, 5],
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

// ── Single-Run: Split Chart (single task) ──

function createSingleSplitChart(canvas, data, splitName, title, existingChart, showMin = false, showMax = false) {
    const sorted = [...data].filter(d => d.split === splitName).sort((a, b) => a.step - b.step);
    const color = SPLIT_COLORS[splitName] || SPLIT_COLORS.train;
    const coreDatasets = [{
        label: `${splitName.charAt(0).toUpperCase() + splitName.slice(1)} [Solid]`,
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

// ── Multitask: All-tasks Overlay Chart ─────
/**
 * Shows all tasks in one chart, each task as a colored line.
 * Each task gets its own color; train=solid, validation=dashed.
 */
function createMultitaskOverlayChart(canvas, data, title, taskFilter, existingChart, showMin = false, showMax = false) {
    const allowedTasks = taskFilter ? (Array.isArray(taskFilter) ? taskFilter : [taskFilter]) : null;
    let allTasks = extractTaskNames(data);
    let tasksToPlot = allTasks;
    if (allowedTasks) {
        tasksToPlot = allTasks.filter(t => allowedTasks.includes(t) || t === SINGLE_TASK);
    }

    const coreDatasets = [];

    tasksToPlot.forEach(taskName => {
        const taskColorIdx = allTasks.indexOf(taskName);
        const taskData = filterByTask(data, taskName);
        const color = TASK_COLORS[taskColorIdx % TASK_COLORS.length];
        const label = taskLabel(taskName);

        // train split
        const trainSorted = taskData.filter(d => d.split === 'train').sort((a, b) => a.step - b.step);
        if (trainSorted.length > 0) {
            coreDatasets.push({
                label: allTasks.length > 1 ? `${label} — Train [Solid]` : 'Train [Solid]',
                data: trainSorted.map(d => ({ x: d.step, y: d.value })),
                borderColor: color.border, backgroundColor: color.bg,
                borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
                borderDash: [],
            });
        }
        // validation split
        const valSorted = taskData.filter(d => d.split === 'validation').sort((a, b) => a.step - b.step);
        if (valSorted.length > 0) {
            coreDatasets.push({
                label: allTasks.length > 1 ? `${label} — Val [Dashed]` : 'Validation [Dashed]',
                data: valSorted.map(d => ({ x: d.step, y: d.value })),
                borderColor: color.border, backgroundColor: 'rgba(0,0,0,0)',
                borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: false,
                borderDash: [5, 3],
            });
        }
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

// ── Multitask: Split Chart ──────────────────
/**
 * Shows a single split for all tasks.
 */
function createMultitaskSplitChart(canvas, data, splitName, title, taskFilter, existingChart, showMin = false, showMax = false) {
    const allowedTasks = taskFilter ? (Array.isArray(taskFilter) ? taskFilter : [taskFilter]) : null;
    let allTasks = extractTaskNames(data);
    let tasksToPlot = allTasks;
    if (allowedTasks) {
        tasksToPlot = allTasks.filter(t => allowedTasks.includes(t) || t === SINGLE_TASK);
    }
    const coreDatasets = [];

    tasksToPlot.forEach(taskName => {
        const taskColorIdx = allTasks.indexOf(taskName);
        const taskData = filterByTask(data, taskName).filter(d => d.split === splitName).sort((a, b) => a.step - b.step);
        if (taskData.length === 0) return;
        const color = TASK_COLORS[taskColorIdx % TASK_COLORS.length];
        coreDatasets.push({
            label: `${taskLabel(taskName)} [Solid]`,
            data: taskData.map(d => ({ x: d.step, y: d.value })),
            borderColor: color.border, backgroundColor: color.bg,
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, fill: true,
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

// ── Multi-Run: Comparison Chart ─────────────

function createComparisonChart(canvas, runsData, splitFilter, title, existingChart, showMin = false, showMax = false, taskFilters = null) {
    const coreDatasets = [];
    let colorIdx = 0;

    // Convert taskFilters to an array if it isn't one and isn't null
    const allowedTasks = taskFilters ? (Array.isArray(taskFilters) ? taskFilters : [taskFilters]) : null;

    Object.entries(runsData).forEach(([runId, { data, label }]) => {
        const runColor = RUN_COLORS[colorIdx % RUN_COLORS.length];
        colorIdx++;

        // Determine what tasks are actually in this run's data that match our filter
        let allTasks = extractTaskNames(data);
        let tasksToPlot = allTasks;
        if (allowedTasks) {
            tasksToPlot = allTasks.filter(t => allowedTasks.includes(t) || t === SINGLE_TASK);
        }

        const splits = splitFilter ? [splitFilter] : ['train', 'validation'];

        tasksToPlot.forEach((task) => {
            const taskIdx = allTasks.indexOf(task);
            const taskData = filterByTask(data, task);

            const dashPatterns = [[], [5, 5], [2, 2], [10, 5], [5, 2, 2, 2]];
            const dashNames = ["Solid", "Dashed", "Dotted", "Long-Dash", "Dash-Dot"];
            const runDash = dashPatterns[taskIdx % dashPatterns.length];
            const runDashName = dashNames[taskIdx % dashNames.length];

            splits.forEach(sp => {
                const filtered = taskData.filter(d => d.split === sp).sort((a, b) => a.step - b.step);
                if (filtered.length === 0) return;

                // Solid for train, dashed for validation if no specific task dash is needed, 
                // but if a specific task dash is used, validation becomes dotted to avoid conflict
                let finalDash = runDash;
                let lineInfo = runDashName;

                if (!splitFilter && sp === 'validation') {
                    if (runDash.length === 0) {
                        finalDash = [5, 5];
                        lineInfo = "Dashed";
                    } else {
                        finalDash = [2, 4];
                        lineInfo = "Dotted";
                    }
                }

                let dsLabel = `${label} [${sp}, ${lineInfo}]`;
                if (tasksToPlot.length > 1 && task !== SINGLE_TASK) {
                    dsLabel = `${label} - ${taskLabel(task)} [${sp}, ${lineInfo}]`;
                }

                coreDatasets.push({
                    label: dsLabel,
                    data: filtered.map(d => ({ x: d.step, y: d.value })),
                    borderColor: runColor.border,
                    backgroundColor: sp === 'validation' ? 'rgba(0,0,0,0)' : runColor.bg,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.3,
                    fill: sp === 'train',
                    borderDash: finalDash
                });
            });
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