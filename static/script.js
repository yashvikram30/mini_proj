// API Base URL (assuming running locally on the same port)
const API_BASE = '/api';

// Chart Instance
let aqiChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch Cities
    await fetchCities();

    // 2. Fetch Initial Timeseries and Summary (Global/All)
    loadTimeseries();

    // 4. Setup Listeners
    document.getElementById('city-selector').addEventListener('change', loadTimeseries);

    document.getElementById('predict-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handlePrediction();
    });
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

async function fetchSummary(city = 'all') {
    try {
        const response = await fetch(`${API_BASE}/summary/${city}`);
        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        // Animate numbers optionally, or just set them
        document.getElementById('kpi-avg-aqi').innerText = data.avg_aqi;
        document.getElementById('kpi-max-aqi').innerText = data.max_aqi;
        document.getElementById('kpi-severe').innerText = data.severe_days.toLocaleString();
        document.getElementById('kpi-records').innerText = data.total_records.toLocaleString();

    } catch (err) {
        console.error("Failed to fetch summary:", err);
    }
}

async function loadTimeseries() {
    const city = document.getElementById('city-selector').value;

    // Fetch the summary for the specific city and update the KPIs
    fetchSummary(city);

    try {
        const response = await fetch(`${API_BASE}/timeseries/${city}`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        renderChart(data.dates, data.aqi);

    } catch (err) {
        console.error("Failed to load timeseries:", err);
    }
}

function renderChart(labels, dataPoints) {
    const ctx = document.getElementById('aqiChart').getContext('2d');

    if (aqiChart) {
        aqiChart.destroy();
    }

    // Monochrome Apple-style Palette
    const lineColor = '#1D1D1F';
    const bgColor = 'rgba(29, 29, 31, 0.05)';

    aqiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average AQI',
                data: dataPoints,
                borderColor: lineColor,
                backgroundColor: bgColor,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.2 // Smooth curves
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
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
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: '#86868B',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    border: { display: false },
                    grid: {
                        color: '#E5E5E7',
                        drawBorder: false,
                    },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: '#86868B',
                        padding: 10
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}

async function handlePrediction() {
    const btn = document.getElementById('predict-btn');
    const OriginalText = btn.innerText;

    btn.innerText = 'Analyzing...';
    btn.disabled = true;

    const payload = {
        t2m: parseFloat(document.getElementById('t2m').value),
        d2m: parseFloat(document.getElementById('d2m').value),
        sp: parseFloat(document.getElementById('sp').value),
        blh: parseFloat(document.getElementById('blh').value),
        wind_speed: parseFloat(document.getElementById('wind_speed').value),
        city: document.getElementById('city-selector').value
    };

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.predicted_aqi !== undefined) {
            const resBox = document.getElementById('prediction-result');
            resBox.classList.remove('hidden');
            document.getElementById('predicted-aqi-value').innerText = data.predicted_aqi;
        } else {
            alert("Error in prediction: " + JSON.stringify(data));
        }

    } catch (err) {
        console.error("Prediction failed:", err);
        alert("Prediction request failed.");
    } finally {
        btn.innerText = OriginalText;
        btn.disabled = false;
    }
}
