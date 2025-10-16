let currentFilters = {};
let charts = {};

async function fetchJSON(path, params = {}) {
	const url = new URL(path, window.location.origin);
	Object.keys(params).forEach(key => {
		if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
			url.searchParams.append(key, params[key]);
		}
	});
	const res = await fetch(url);
	return await res.json();
}

function getCurrentFilters() {
	const startDate = document.getElementById("start-date").value;
	const endDate = document.getElementById("end-date").value;
	const minFare = document.getElementById("min-fare").value;
	const maxFare = document.getElementById("max-fare").value;
	const hour = document.getElementById("hour-filter").value;
	
	return {
		start: startDate || null,
		end: endDate || null,
		min_fare: minFare ? parseFloat(minFare) : null,
		max_fare: maxFare ? parseFloat(maxFare) : null,
		hour: hour ? parseInt(hour) : null
	};
}

async function loadKpis() {
	const filters = getCurrentFilters();
	const k = await fetchJSON("/api/kpis", filters);
	document.getElementById("kpi-count").textContent = k.trip_count.toLocaleString();
	document.getElementById("kpi-speed").textContent = k.avg_speed_kmh.toFixed(1);
	document.getElementById("kpi-fpk").textContent = k.avg_fare_per_km.toFixed(2);
}

async function renderSpeedByHour() {
	const data = await fetchJSON("/api/speed_by_hour");
	const ctx = document.getElementById("chart-speed");
	
	if (charts.speed) {
		charts.speed.destroy();
	}
	
	const labels = data.map(d => d.hour);
	const speeds = data.map(d => d.avg_speed_kmh);
	charts.speed = new Chart(ctx, {
		type: 'line',
		data: { 
			labels, 
			datasets: [{ 
				label: 'Avg Speed (km/h)', 
				data: speeds, 
				borderColor: '#0d6efd', 
				backgroundColor: 'rgba(13,110,253,0.2)', 
				fill: true, 
				tension: 0.25 
			}] 
		},
		options: { 
			scales: { y: { beginAtZero: true } },
			responsive: true,
			maintainAspectRatio: false
		}
	});
}

async function renderFareByWeekday() {
	const data = await fetchJSON("/api/fare_by_weekday");
	const ctx = document.getElementById("chart-fare-weekday");
	
	if (charts.fareWeekday) {
		charts.fareWeekday.destroy();
	}
	
	const labels = data.map(d => d.weekday);
	const fares = data.map(d => d.avg_fare_per_km);
	charts.fareWeekday = new Chart(ctx, {
		type: 'bar',
		data: { 
			labels, 
			datasets: [{ 
				label: 'Avg Fare per KM ($)', 
				data: fares, 
				backgroundColor: 'rgba(40, 167, 69, 0.8)',
				borderColor: '#28a745',
				borderWidth: 1
			}] 
		},
		options: { 
			scales: { y: { beginAtZero: true } },
			responsive: true,
			maintainAspectRatio: false
		}
	});
}

async function renderTopPickupZones() {
	const data = await fetchJSON("/api/top_pickup_zones", { k: 20 });
	const ctx = document.getElementById("chart-pickup-zones");
	
	if (charts.pickupZones) {
		charts.pickupZones.destroy();
	}
	
	const labels = data.map((d, i) => `Zone ${i + 1}`);
	const counts = data.map(d => d.count);
	
	charts.pickupZones = new Chart(ctx, {
		type: 'bar',
		data: { 
			labels, 
			datasets: [{ 
				label: 'Pickup Count', 
				data: counts, 
				backgroundColor: 'rgba(255, 193, 7, 0.8)',
				borderColor: '#ffc107',
				borderWidth: 1
			}] 
		},
		options: { 
			scales: { y: { beginAtZero: true } },
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					display: false
				}
			}
		}
	});
}

async function loadAnomalyDetection() {
	const data = await fetchJSON("/api/anomaly_detection");
	
	document.getElementById("anomaly-stats").innerHTML = `
		<strong>Anomaly Detection Results:</strong><br>
		Total checked: ${data.total_checked} trips<br>
		Anomalies found: ${data.anomalies.length}<br>
		Threshold: Z-score > ${data.threshold}
	`;
	
	const anomalyList = document.getElementById("anomaly-list");
	anomalyList.innerHTML = data.anomalies.map(anomaly => `
		<div class="anomaly-item">
			<strong>Trip ${anomaly.index + 1}:</strong><br>
			Speed: ${anomaly.speed_kmh.toFixed(1)} km/h (Z: ${anomaly.speed_z_score.toFixed(2)})<br>
			Fare/km: $${anomaly.fare_per_km.toFixed(2)} (Z: ${anomaly.fare_z_score.toFixed(2)})<br>
			Distance: ${anomaly.distance_km.toFixed(2)} km (Z: ${anomaly.distance_z_score.toFixed(2)})
		</div>
	`).join('');
}

function clearFilters() {
	document.getElementById("start-date").value = "";
	document.getElementById("end-date").value = "";
	document.getElementById("min-fare").value = "";
	document.getElementById("max-fare").value = "";
	document.getElementById("hour-filter").value = "";
}

async function applyFilters() {
	currentFilters = getCurrentFilters();
	await loadKpis();
	// Note: Other charts don't support filtering yet, but KPIs do
}

// Event listeners
document.getElementById("apply-filters").addEventListener("click", applyFilters);
document.getElementById("clear-filters").addEventListener("click", () => {
	clearFilters();
	applyFilters();
});

// Initialize dashboard
async function initDashboard() {
	await loadKpis();
	await renderSpeedByHour();
	await renderFareByWeekday();
	await renderTopPickupZones();
	await loadAnomalyDetection();
}

initDashboard();
