const API_BASE = '/api';

// Chart Instances
let monthlyChart = null;
let distributionChart = null;
let correlationChart = null;

// Apple-style modern monochromatic palette
const CHOSEN_BRAND_COLOR = '#1D1D1F';
const CHOSEN_BRAND_BG = 'rgba(29, 29, 31, 0.05)';
const NEUTRAL_COLORS = [
    '#1D1D1F', // Black
    '#86868B', // Gray
    '#E5E5E7', // Light Gray
    '#F5F5F7'  // Off white
];

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Cities for Selector
    await fetchCities();

    // 2. Initial Data Load
    loadAllAnalytics();

    // 3. Listen for City Changes
    document.getElementById('city-selector').addEventListener('change', loadAllAnalytics);
});

async function fetchCities() {
    try {
        const response = await fetch(`${API_BASE}/cities`);
        const data = await response.json();

        if (data.cities) {
            const selector = document.getElementById('city-selector');
            data.cities.forEach(city => {
                const opt = document.createElement('option');
                opt.value = city;
                opt.text = city;
                selector.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Failed to fetch cities:", err);
    }
}

function loadAllAnalytics() {
    const city = document.getElementById('city-selector').value;
    fetchMonthlySeasonality(city);
    fetchDistribution(city);
    fetchCorrelation(city);
}

// ============================================
// 1. Monthly Seasonality Bar Chart
// ============================================
async function fetchMonthlySeasonality(city) {
    try {
        const response = await fetch(`${API_BASE}/analytics/${city}/monthly`);
        const data = await response.json();

        if (!data.error) {
            renderMonthlyChart(data.labels, data.values);
        }
    } catch (err) {
        console.error("Failed to fetch monthly data", err);
    }
}

function renderMonthlyChart(labels, values) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    if (monthlyChart) monthlyChart.destroy();

    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average AQI',
                data: values,
                backgroundColor: CHOSEN_BRAND_COLOR,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1D1D1F',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 14 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: '#86868B' }
                },
                y: {
                    border: { display: false },
                    grid: { color: '#E5E5E7', drawBorder: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: '#86868B', padding: 10 }
                }
            }
        }
    });
}

// ============================================
// 2. AQI Distribution Doughnut Chart
// ============================================
async function fetchDistribution(city) {
    try {
        const response = await fetch(`${API_BASE}/analytics/${city}/distribution`);
        const data = await response.json();

        if (!data.error) {
            renderDistributionChart(data.labels, data.values);
        }
    } catch (err) {
        console.error("Failed to fetch distribution data", err);
    }
}

function renderDistributionChart(labels, values) {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    if (distributionChart) distributionChart.destroy();

    // Map categories to stylistic monochrome/grey palette
    const colors = [
        '#F5F5F7', // Good
        '#E5E5E7', // Moderate
        '#86868B', // Unhealthy
        '#1D1D1F'  // Severe
    ];

    distributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#FFFFFF',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { family: 'Inter', size: 12 },
                        color: '#1D1D1F',
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: '#1D1D1F',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 14 },
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function (context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed !== null) {
                                label += context.parsed + ' Days';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// ============================================
// 3. Feature Correlation Chart
// ============================================
async function fetchCorrelation(city) {
    try {
        const response = await fetch(`${API_BASE}/analytics/${city}/correlation`);
        const data = await response.json();

        if (!data.error) {
            renderCorrelationChart(data.labels, data.values);
        }
    } catch (err) {
        console.error("Failed to fetch correlation data", err);
    }
}

function renderCorrelationChart(labels, values) {
    const ctx = document.getElementById('correlationChart').getContext('2d');
    if (correlationChart) correlationChart.destroy();

    // Map internal codes to human readables
    const labelMap = {
        't2m': 'Temperature',
        'd2m': 'Dewpoint',
        'wind_speed': 'Wind Speed',
        'sp': 'Surface Pressure',
        'blh': 'Boundary Layer'
    };

    const displayLabels = labels.map(l => labelMap[l] || l);

    // Color code based on positive/negative correlation
    const bgColors = values.map(v => v >= 0 ? CHOSEN_BRAND_COLOR : '#86868B');

    correlationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: displayLabels,
            datasets: [{
                label: 'Pearson Correlation',
                data: values,
                backgroundColor: bgColors,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y', // horizontal bar chart
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1D1D1F',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 14 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E5E7', drawBorder: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: '#86868B' }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#1D1D1F' }
                }
            }
        }
    });
}
