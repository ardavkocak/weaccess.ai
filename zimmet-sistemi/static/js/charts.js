/* Chart.js grafik olusturma yardimcilari - Dashboard ve Raporlar sayfalarinda kullanilir. */
function renderPieChart(canvasId, labels, data, colors) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{ data: data, backgroundColor: colors }],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "bottom" } },
        },
    });
}

function renderBarChart(canvasId, labels, data, label, color) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{ label: label, data: data, backgroundColor: color, borderRadius: 6 }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });
}

function renderLineChart(canvasId, labels, data, label, color) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: label,
                    data: data,
                    borderColor: color,
                    backgroundColor: color + "33",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });
}
