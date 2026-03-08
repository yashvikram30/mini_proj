const API_BASE = '/api';

let currentPage = 1;
let totalPages = 1;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', async () => {
    await fetchCities();
    loadRawData();

    document.getElementById('city-selector').addEventListener('change', () => {
        currentPage = 1;
        loadRawData();
    });

    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadRawData();
        }, 400);
    });

    document.getElementById('btn-prev').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadRawData();
        }
    });

    document.getElementById('btn-next').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadRawData();
        }
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

async function loadRawData() {
    const city = document.getElementById('city-selector').value;
    const search = document.getElementById('search-input').value;

    const params = new URLSearchParams({
        city: city,
        page: currentPage,
        per_page: 50,
        search: search
    });

    try {
        const response = await fetch(`${API_BASE}/rawdata?${params}`);

        if (response.status === 503) {
            // Server still loading
            setTimeout(() => loadRawData(), 3000);
            return;
        }

        if (!response.ok) {
            showEmpty(true);
            return;
        }

        const data = await response.json();

        if (data.error) {
            showEmpty(true);
            return;
        }

        totalPages = data.total_pages;
        currentPage = data.current_page;

        renderTable(data.display_columns, data.rows);
        updatePagination(data);
        showEmpty(false);

    } catch (err) {
        console.error("Failed to load raw data:", err);
        showEmpty(true);
    }
}

function renderTable(columns, rows) {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');

    // Build header
    let headerHTML = '<tr>';
    columns.forEach(col => {
        headerHTML += `<th>${col}</th>`;
    });
    headerHTML += '</tr>';
    thead.innerHTML = headerHTML;

    // Build body
    let bodyHTML = '';
    rows.forEach(row => {
        bodyHTML += '<tr>';
        row.forEach((cell, idx) => {
            const value = cell !== null && cell !== undefined ? cell : '—';
            // Highlight AQI cells with category color
            const colName = columns[idx];
            if (colName === 'AQI' && typeof cell === 'number') {
                const cls = getAqiBadgeClass(cell);
                bodyHTML += `<td><span class="aqi-badge ${cls}">${value}</span></td>`;
            } else {
                bodyHTML += `<td>${value}</td>`;
            }
        });
        bodyHTML += '</tr>';
    });
    tbody.innerHTML = bodyHTML;
}

function getAqiBadgeClass(aqi) {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 200) return 'aqi-unhealthy';
    return 'aqi-severe';
}

function updatePagination(data) {
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const pageText = document.getElementById('pagination-text');
    const recordsBadge = document.getElementById('total-records-badge');
    const pageInfoBadge = document.getElementById('page-info-badge');

    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    pageText.textContent = `Page ${currentPage} of ${totalPages}`;
    recordsBadge.textContent = `${data.total_rows.toLocaleString()} records`;
    pageInfoBadge.textContent = `Showing ${data.rows.length} of ${data.total_rows.toLocaleString()}`;
}

function showEmpty(visible) {
    const table = document.getElementById('data-table');
    const empty = document.getElementById('table-empty');

    if (visible) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
    } else {
        table.classList.remove('hidden');
        empty.classList.add('hidden');
    }
}
