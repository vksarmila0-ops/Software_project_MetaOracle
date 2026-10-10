/**
 * Chart.js Integration for MetaOracle Visualizations
 */

const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

/**
 * Renders the Recent Test Runs Pass Rate Trend Line Chart
 */
function renderTrendChart(canvasId, runs) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  const sortedRuns = [...runs].reverse();
  const labels = sortedRuns.map((r, i) => `#${r.id} (${r.function_name.slice(0, 10)})`);
  const passRates = sortedRuns.map(r => r.pass_rate);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['No Runs Yet'],
      datasets: [{
        label: 'Pass Rate (%)',
        data: passRates.length ? passRates : [100],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#818cf8',
        pointBorderColor: '#ffffff',
        pointRadius: 4,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8',
          borderColor: '#334155',
          borderWidth: 1,
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', maxRotation: 45 }
        }
      }
    }
  });
}

/**
 * Renders the Mutation Score Doughnut Chart
 */
function renderMutationScoreChart(canvasId, killed, survived, errorCount = 0) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Killed Mutants', 'Survived Mutants', 'Execution Errors'],
      datasets: [{
        data: [killed, survived, errorCount],
        backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
        borderWidth: 0,
        hoverOffset: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#cbd5e1', padding: 15, font: { size: 12 } }
        }
      }
    }
  });
}

/**
 * Renders Comparative Benchmark Grouped Bar Chart
 */
function renderBenchmarkChart(canvasId, results) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  const labels = results.map(r => r.technique_name);
  const detectionRates = results.map(r => r.detection_rate);
  const testsExecuted = results.map(r => r.tests_executed);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Bug Detection Rate (%)',
          data: detectionRates,
          backgroundColor: ['rgba(239, 68, 68, 0.8)', 'rgba(245, 158, 11, 0.8)', 'rgba(16, 185, 129, 0.8)'],
          borderColor: ['#ef4444', '#f59e0b', '#10b981'],
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: 'yRate',
        },
        {
          label: 'Tests Executed',
          data: testsExecuted,
          backgroundColor: 'rgba(99, 102, 241, 0.4)',
          borderColor: '#6366f1',
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: 'yCount',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#cbd5e1' }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
        }
      },
      scales: {
        x: {
          ticks: { color: '#cbd5e1' },
          grid: { display: false }
        },
        yRate: {
          type: 'linear',
          position: 'left',
          min: 0,
          max: 100,
          ticks: { color: '#10b981' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          title: { display: true, text: 'Detection Rate (%)', color: '#10b981' }
        },
        yCount: {
          type: 'linear',
          position: 'right',
          ticks: { color: '#818cf8' },
          grid: { display: false },
          title: { display: true, text: 'Total Tests', color: '#818cf8' }
        }
      }
    }
  });
}
