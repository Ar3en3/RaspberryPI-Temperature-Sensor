var socket = io();
socket.on('sensor_update', function(data) {
document.getElementById('timestamp').innerText = data.timestamp;
document.getElementById('temperature').innerText = parseFloat(data.temperature).toFixed(2);
document.getElementById('humidity').innerText = parseFloat(data.humidity).toFixed(2);
document.getElementById('pressure').innerText = parseFloat(data.pressure).toFixed(2);
document.getElementById('temp-warning').innerText = (data.warnings && data.warnings.temperature) ? "Warning!" : "";
document.getElementById('hum-warning').innerText = (data.warnings && data.warnings.humidity) ? "Warning!" : "";
document.getElementById('pres-warning').innerText = (data.warnings && data.warnings.pressure) ? "Warning!" : "";
});
document.getElementById('thresholdForm').addEventListener('submit', function(e) {
e.preventDefault();
var formData = new FormData(e.target);
var thresholds = {};
formData.forEach(function(value, key) {
thresholds[key] = value;
});
fetch('/update_thresholds', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(thresholds)
})
.then(response => response.json())
.then(data => alert("Thresholds updated successfully!"))
.catch(error => console.error('Error updating thresholds:', error));
});
var tempChart = null;
function fetchHistoricalDataAndUpdateChart() {
fetch('/history')
.then(response => response.json())
.then(data => {
if (data.length < 2) {
console.warn("Not enough data to render chart.");
return;
}
let timestamps = data.map(record => new Date(record.timestamp + "Z"));
let temperatures = data.map(record => record.temperature);
let xValues = timestamps.map(date => date.getTime());
let n = xValues.length;
let sumX = xValues.reduce((acc, val) => acc + val, 0);
let sumY = temperatures.reduce((acc, val) => acc + val, 0);
let sumXY = 0, sumXX = 0;
for (let i = 0; i < n; i++) {
sumXY += xValues[i] * temperatures[i];
sumXX += xValues[i] * xValues[i];
}
let m = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
let b = (sumY - m * sumX) / n;
let regressionData = xValues.map(x => m * x + b);
let labels = timestamps.map(date => date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
var ctx = document.getElementById('tempChart').getContext('2d');
if (!tempChart) {
tempChart = new Chart(ctx, {
type: 'line',
data: {
labels: labels,
datasets: [
{ label: 'Temperature (°C)', data: temperatures, borderColor: 'blue', backgroundColor: 'rgba(0,0,255,0.1)', fill: false, tension: 0.1 },
{ label: 'Trend Line', data: regressionData, borderColor: 'red', backgroundColor: 'rgba(255,0,0,0.1)', fill: false, borderDash: [5,5], tension: 0.1 }
]
},
options: { responsive: true, scales: { x: { type: 'time', time: { unit: 'minute', displayFormats: { minute: 'HH:mm' }}, title: { display: true, text: 'Time' }}, y: { beginAtZero: false, title: { display: true, text: 'Temperature (°C)' }}}}
});
} else {
tempChart.data.labels = labels;
tempChart.data.datasets[0].data = temperatures;
tempChart.data.datasets[1].data = regressionData;
tempChart.update();
}
let threshold = parseFloat(document.querySelector('input[name="temperature_max"]').value);
let lastTemp = temperatures[temperatures.length - 1];
let predictedDate = null;
if (m > 0 && lastTemp < threshold) {
let predictedNumeric = (threshold - b) / m;
predictedDate = new Date(predictedNumeric);
}
if (predictedDate) {
document.getElementById('prediction').innerText = "Predicted time to exceed " + threshold + "°C: " + predictedDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
} else {
document.getElementById('prediction').innerText = "";
}
})
.catch(error => console.error("Error fetching historical data:", error));
}
fetchHistoricalDataAndUpdateChart();
setInterval(fetchHistoricalDataAndUpdateChart, 10000);
