from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    # Comment out DROP TABLE after first run to persist data
    # c.execute('DROP TABLE IF EXISTS locations')
    c.execute('''CREATE TABLE IF NOT EXISTS locations (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 type TEXT,
                 lat REAL,
                 lon REAL,
                 speed REAL,
                 timestamp TEXT,
                 days TEXT,
                 time_from TEXT,
                 time_to TEXT)''')
    conn.commit()
    conn.close()

# HTML template with Tailwind CSS, FontAwesome, and OpenStreetMap
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tanjore District Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { 
            background-color: #121212; 
            color: #e0e0e0; 
            font-family: 'Roboto', sans-serif; 
            margin: 0; 
            overflow: hidden; 
        }
        #map { 
            height: 100vh; 
            width: calc(100% - 300px); 
            margin-left: 300px; 
        }
        .sidebar { 
            width: 300px; 
            background-color: #1e1e1e; 
            position: fixed; 
            height: 100vh; 
            z-index: 1000; 
            overflow-y: auto; 
            border-right: 1px solid #2d2d2d; 
            transition: width 0.3s ease; 
        }
        .sidebar.collapsed { width: 60px; }
        .sidebar.collapsed .sidebar-content { display: none; }
        .sidebar-header { 
            background-color: #252525; 
            padding: 16px; 
            border-bottom: 1px solid #2d2d2d; 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
        }
        .sidebar-content { padding: 20px; }
        .alert { 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            z-index: 2000; 
            background-color: #2d2d2d; 
            color: #e0e0e0; 
            padding: 12px 20px; 
            border-radius: 4px; 
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); 
            animation: slideIn 0.3s ease-out; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            border-left: 4px solid; 
        }
        .alert.success { border-left-color: #4caf50; }
        .alert.error { border-left-color: #f44336; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .custom-icon { 
            background: #2d2d2d; 
            border-radius: 50%; 
            width: 28px; 
            height: 28px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #42a5f5; 
            font-size: 14px; 
            border: 1px solid #424242; 
        }
        .input-field { 
            background-color: #252525; 
            border: 1px solid #424242; 
            color: #e0e0e0; 
            padding: 8px; 
            border-radius: 4px; 
            width: 100%; 
            transition: border-color 0.2s ease; 
        }
        .input-field:focus { border-color: #42a5f5; outline: none; }
        .btn { 
            background-color: #1976d2; 
            color: #fff; 
            padding: 8px 16px; 
            border-radius: 4px; 
            transition: background-color 0.2s ease; 
            display: flex; 
            align-items: center; 
            gap: 6px; 
        }
        .btn:hover { background-color: #1e88e5; }
        .btn-danger { background-color: #d32f2f; }
        .btn-danger:hover { background-color: #e53935; }
        .btn-secondary { background-color: #424242; }
        .btn-secondary:hover { background-color: #616161; }
        .popup-content { 
            background: #1e1e1e; 
            border-radius: 6px; 
            padding: 16px; 
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); 
            color: #e0e0e0; 
            width: 260px; 
            border: 1px solid #2d2d2d; 
        }
        .tab { display: none; }
        .tab.active { display: block; }
        .tab-button { 
            background-color: #2d2d2d; 
            padding: 6px 12px; 
            border-radius: 4px; 
            margin-right: 6px; 
            cursor: pointer; 
            transition: background-color 0.2s ease; 
        }
        .tab-button.active { background-color: #42a5f5; color: #fff; }
        .tab-button:hover { background-color: #616161; }
        .location-card { 
            background-color: #252525; 
            padding: 12px; 
            border-radius: 4px; 
            margin-bottom: 12px; 
            border: 1px solid #2d2d2d; 
            transition: background-color 0.2s ease; 
        }
        .location-card:hover { background-color: #2d2d2d; }
        .icon-text { display: flex; align-items: center; gap: 8px; }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h1 class="text-lg font-semibold"><i class="fas fa-globe-asia mr-2"></i>Tanjore Dashboard</h1>
            <button onclick="toggleSidebar()" class="text-gray-400 hover:text-white"><i class="fas fa-bars"></i></button>
        </div>
        <div class="sidebar-content" id="sidebarContent">
            <div class="mb-6">
                <h2 class="text-md font-medium mb-3 icon-text"><i class="fas fa-map-pin"></i>Add Location</h2>
                <select id="locationType" class="input-field mb-3">
                    <option value="accidents">Accidents</option>
                    <option value="crowded">Crowded</option>
                    <option value="hospitals">Hospital</option>
                    <option value="schools">School</option>
                </select>
                <input type="number" id="speed" class="input-field mb-3" placeholder="Speed (km/h)" min="0" step="0.1">
                <button onclick="enableMarking()" class="btn w-full"><i class="fas fa-plus"></i>Add</button>
                <p id="status" class="text-sm text-gray-400 mt-2"></p>
            </div>
            <div>
                <h2 class="text-md font-medium mb-3 icon-text"><i class="fas fa-list"></i>Locations</h2>
                <div id="locationsList"></div>
            </div>
        </div>
    </div>

    <!-- Map Container -->
    <div id="map"></div>

    <script>
        let map;
        let markingEnabled = false;
        const markers = {};
        const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

        // Custom FontAwesome-based icons
        const icons = {
            accidents: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-exclamation-triangle"></i>', iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] }),
            crowded: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-users"></i>', iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] }),
            hospitals: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-hospital"></i>', iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] }),
            schools: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-school"></i>', iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] })
        };

        // Show alert
        function showAlert(message, type = 'success') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${type}`;
            alertDiv.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2"></i>${message}`;
            document.body.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 3000);
        }

        // Initialize map
        function initMap() {
            map = L.map('map', {
                center: [10.7860, 79.1378],
                zoom: 10,
                minZoom: 10,
                maxBounds: [[10.05, 78.8], [11.2, 79.7]],
                maxBoundsViscosity: 1.0
            });

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(map);

            loadLocations();
            map.on('click', function(e) {
                if (markingEnabled) {
                    const type = document.getElementById('locationType').value;
                    const speed = document.getElementById('speed').value;
                    addMarker(e.latlng.lat, e.latlng.lng, type, speed);
                    fetch('/add_location', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            type: type,
                            lat: e.latlng.lat,
                            lon: e.latlng.lng,
                            speed: speed,
                            timestamp: new Date().toISOString(),
                            days: '',
                            time_from: '',
                            time_to: ''
                        })
                    }).then(response => response.json())
                      .then(data => {
                          if (data.status === 'success') {
                              showAlert('Location added successfully', 'success');
                              loadLocations();
                          }
                      });
                    markingEnabled = false;
                    map.getContainer().style.cursor = '';
                    document.getElementById('speed').value = '';
                    document.getElementById('status').innerText = '';
                }
            });
        }

        // Enable marking mode
        function enableMarking() {
            const speed = document.getElementById('speed').value;
            if (!speed) {
                showAlert('Please enter a speed', 'error');
                document.getElementById('status').innerText = 'Enter a speed';
                document.getElementById('status').className = 'text-sm text-red-400 mt-2';
                return;
            }
            markingEnabled = true;
            map.getContainer().style.cursor = 'crosshair';
            document.getElementById('status').innerText = 'Click to mark location';
            document.getElementById('status').className = 'text-sm text-green-400 mt-2';
        }

        // Toggle sidebar
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
            map.invalidateSize();
        }

        // Load locations
        function loadLocations() {
            fetch('/get_locations')
                .then(response => response.json())
                .then(data => {
                    Object.keys(markers).forEach(id => map.removeLayer(markers[id].marker));
                    Object.assign(markers, {});
                    data.forEach(loc => addMarker(loc.lat, loc.lon, loc.type, loc.speed, loc.timestamp, loc.id, loc.days, loc.time_from, loc.time_to));
                    updateLocationsList();
                });
        }

        // Add marker
        function addMarker(lat, lon, type, speed, timestamp, id = null, days = '', time_from = '', time_to = '') {
            const displayTime = new Date(timestamp).toLocaleString('en-US', { 
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' 
            });
            const markerId = id || Date.now();
            const marker = L.marker([lat, lon], { icon: icons[type] }).addTo(map);

            const dayCheckboxes = daysOfWeek.map(day => `
                <label class="icon-text mb-1">
                    <input type="checkbox" id="day_${day}_${markerId}" ${days.split(',').includes(day) ? 'checked' : ''} ${days === 'Everyday' ? 'disabled' : ''} class="mr-2"> ${day}
                </label>
            `).join('');

            marker.bindPopup(`
                <div class="popup-content">
                    <div class="flex mb-3">
                        <span class="tab-button active" onclick="switchTab('info', ${markerId})"><i class="fas fa-info-circle"></i></span>
                        <span class="tab-button" onclick="switchTab('datetime', ${markerId})"><i class="fas fa-clock"></i></span>
                    </div>
                    <div id="info_${markerId}" class="tab active">
                        <p class="icon-text"><i class="fas fa-layer-group"></i>Type: ${type}</p>
                        <p class="icon-text"><i class="fas fa-tachometer-alt"></i>Speed: <input type="number" id="editSpeed${markerId}" value="${speed}" step="0.1" min="0" class="input-field w-16 inline"> km/h</p>
                        <p class="icon-text"><i class="fas fa-map-marker-alt"></i>Lat: ${lat.toFixed(4)}</p>
                        <p class="icon-text"><i class="fas fa-long-arrow-alt-right"></i>Lon: ${lon.toFixed(4)}</p>
                        <p class="icon-text"><i class="fas fa-calendar-alt"></i>${displayTime}</p>
                        <div class="mt-3 flex gap-2">
                            <button onclick="updateMarker(${markerId}, ${lat}, ${lon}, '${type}')" class="btn"><i class="fas fa-save"></i>Save</button>
                            <button onclick="deleteMarker(${markerId})" class="btn btn-danger"><i class="fas fa-trash"></i>Delete</button>
                        </div>
                    </div>
                    <div id="datetime_${markerId}" class="tab">
                        <p class="font-medium mb-2 icon-text"><i class="fas fa-calendar-day"></i>Schedule</p>
                        <label class="icon-text mb-2">
                            <input type="checkbox" id="everyday_${markerId}" ${days === 'Everyday' ? 'checked' : ''} onchange="toggleEveryday(${markerId})" class="mr-2"> Everyday
                        </label>
                        ${dayCheckboxes}
                        <label class="icon-text mb-2">
                            <input type="checkbox" id="anytime_${markerId}" ${time_from === '00:00' && time_to === '23:59' ? 'checked' : ''} onchange="toggleAnytime(${markerId})" class="mr-2"> Anytime
                        </label>
                        <p class="icon-text"><i class="fas fa-hourglass-start"></i>From: <input type="time" id="timeFrom${markerId}" value="${time_from}" class="input-field w-24 ${time_from === '00:00' && time_to === '23:59' ? 'opacity-50' : ''}" ${time_from === '00:00' && time_to === '23:59' ? 'disabled' : ''}></p>
                        <p class="icon-text"><i class="fas fa-hourglass-end"></i>To: <input type="time" id="timeTo${markerId}" value="${time_to}" class="input-field w-24 ${time_from === '00:00' && time_to === '23:59' ? 'opacity-50' : ''}" ${time_from === '00:00' && time_to === '23:59' ? 'disabled' : ''}></p>
                        <div class="mt-3 flex gap-2">
                            <button onclick="saveDayTime(${markerId}, ${lat}, ${lon}, '${type}')" class="btn"><i class="fas fa-check"></i>Apply</button>
                            <button onclick="clearDayTime(${markerId})" class="btn btn-secondary"><i class="fas fa-times"></i>Clear</button>
                        </div>
                    </div>
                </div>
            `);

            marker.on('popupopen', function() {
                const popup = marker.getPopup();
                L.DomEvent.addListener(popup._contentNode, 'click', L.DomEvent.stopPropagation);
            });

            markers[markerId] = { marker, lat, lon, type, speed, timestamp, days, time_from, time_to, id };
            updateLocationsList();
        }

        // Toggle Everyday
        function toggleEveryday(markerId) {
            const everydayCheckbox = document.getElementById(`everyday_${markerId}`);
            const isChecked = everydayCheckbox.checked;
            daysOfWeek.forEach(day => {
                const checkbox = document.getElementById(`day_${day}_${markerId}`);
                checkbox.disabled = isChecked;
                if (isChecked) checkbox.checked = true;
            });
        }

        // Toggle Anytime
        function toggleAnytime(markerId) {
            const anytimeCheckbox = document.getElementById(`anytime_${markerId}`);
            const timeFrom = document.getElementById(`timeFrom${markerId}`);
            const timeTo = document.getElementById(`timeTo${markerId}`);
            if (anytimeCheckbox.checked) {
                timeFrom.value = '00:00';
                timeTo.value = '23:59';
                timeFrom.disabled = true;
                timeTo.disabled = true;
                timeFrom.classList.add('opacity-50');
                timeTo.classList.add('opacity-50');
            } else {
                timeFrom.disabled = false;
                timeTo.disabled = false;
                timeFrom.classList.remove('opacity-50');
                timeTo.classList.remove('opacity-50');
            }
        }

        // Switch tabs
        function switchTab(tab, markerId) {
            const infoTab = document.getElementById(`info_${markerId}`);
            const datetimeTab = document.getElementById(`datetime_${markerId}`);
            const infoButton = document.querySelector(`#info_${markerId}`).parentElement.querySelector('.tab-button:first-child');
            const datetimeButton = document.querySelector(`#datetime_${markerId}`).parentElement.querySelector('.tab-button:last-child');
            if (tab === 'info') {
                infoTab.classList.add('active');
                datetimeTab.classList.remove('active');
                infoButton.classList.add('active');
                datetimeButton.classList.remove('active');
            } else {
                infoTab.classList.remove('active');
                datetimeTab.classList.add('active');
                infoButton.classList.remove('active');
                datetimeButton.classList.add('active');
            }
        }

        // Update marker speed
        function updateMarker(id, lat, lon, type) {
            const newSpeed = document.getElementById(`editSpeed${id}`).value;
            if (!newSpeed) {
                showAlert('Please enter a speed', 'error');
                return;
            }
            fetch('/update_location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: markers[id].id,
                    lat: lat,
                    lon: lon,
                    type: type,
                    speed: newSpeed,
                    timestamp: markers[id].timestamp,
                    days: markers[id].days,
                    time_from: markers[id].time_from,
                    time_to: markers[id].time_to
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      showAlert('Speed updated', 'success');
                      loadLocations();
                  }
              });
        }

        // Save day and time
        function saveDayTime(id, lat, lon, type) {
            const everydayCheckbox = document.getElementById(`everyday_${id}`);
            const anytimeCheckbox = document.getElementById(`anytime_${id}`);
            let selectedDays = everydayCheckbox.checked ? 'Everyday' : daysOfWeek.filter(day => document.getElementById(`day_${day}_${id}`).checked).join(',');
            let timeFrom = document.getElementById(`timeFrom${id}`).value;
            let timeTo = document.getElementById(`timeTo${id}`).value;

            if (anytimeCheckbox.checked) {
                timeFrom = '00:00';
                timeTo = '23:59';
            }

            fetch('/update_location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: markers[id].id,
                    lat: lat,
                    lon: lon,
                    type: type,
                    speed: markers[id].speed,
                    timestamp: markers[id].timestamp,
                    days: selectedDays,
                    time_from: timeFrom,
                    time_to: timeTo
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      showAlert('Schedule updated', 'success');
                      loadLocations();
                  } else {
                      showAlert('Update failed', 'error');
                  }
              });
        }

        // Clear day and time
        function clearDayTime(id) {
            fetch('/update_location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: markers[id].id,
                    lat: markers[id].lat,
                    lon: markers[id].lon,
                    type: markers[id].type,
                    speed: markers[id].speed,
                    timestamp: markers[id].timestamp,
                    days: '',
                    time_from: '',
                    time_to: ''
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      showAlert('Schedule cleared', 'success');
                      loadLocations();
                  }
              });
        }

        // Delete marker
        function deleteMarker(id) {
            if (!markers[id].id) {
                showAlert('Cannot delete unsaved marker', 'error');
                return;
            }
            fetch('/delete_location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: markers[id].id })
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      showAlert('Location deleted', 'success');
                      loadLocations();
                  }
              });
        }

        // Update locations list
        function updateLocationsList() {
            const list = document.getElementById('locationsList');
            list.innerHTML = '';
            Object.values(markers).forEach(loc => {
                const displayTime = new Date(loc.timestamp).toLocaleString('en-US', { 
                    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                });
                list.innerHTML += `
                    <div class="location-card">
                        <p class="icon-text"><i class="fas fa-layer-group"></i>${loc.type}</p>
                        <p class="icon-text"><i class="fas fa-map-marker-alt"></i>Lat: ${loc.lat.toFixed(4)}, Lon: ${loc.lon.toFixed(4)}</p>
                        <p class="icon-text"><i class="fas fa-tachometer-alt"></i>${loc.speed} km/h</p>
                        <p class="icon-text"><i class="fas fa-calendar-alt"></i>${displayTime}</p>
                        <p class="icon-text"><i class="fas fa-calendar-day"></i>${loc.days || 'None'}</p>
                        <p class="icon-text"><i class="fas fa-clock"></i>${loc.time_from && loc.time_to ? `${loc.time_from} - ${loc.time_to}` : 'Not set'}</p>
                    </div>
                `;
            });
        }

        document.addEventListener('DOMContentLoaded', initMap);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/add_location', methods=['POST'])
def add_location():
    data = request.get_json()
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute('INSERT INTO locations (type, lat, lon, speed, timestamp, days, time_from, time_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (data['type'], data['lat'], data['lon'], float(data['speed']), data['timestamp'], data['days'], data['time_from'], data['time_to']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/get_locations')
def get_locations():
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute('SELECT id, type, lat, lon, speed, timestamp, days, time_from, time_to FROM locations')
    rows = c.fetchall()
    conn.close()
    locations = [{'id': r[0], 'type': r[1], 'lat': r[2], 'lon': r[3], 'speed': r[4], 'timestamp': r[5], 'days': r[6], 'time_from': r[7], 'time_to': r[8]} for r in rows]
    return jsonify(locations)

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute('UPDATE locations SET type=?, lat=?, lon=?, speed=?, timestamp=?, days=?, time_from=?, time_to=? WHERE id=?',
              (data['type'], data['lat'], data['lon'], float(data['speed']), data['timestamp'], data['days'], data['time_from'], data['time_to'], data['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/delete_location', methods=['POST'])
def delete_location():
    data = request.get_json()
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute('DELETE FROM locations WHERE id=?', (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)