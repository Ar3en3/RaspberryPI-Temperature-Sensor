import os
import sqlite3
import threading
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "your_secret_key")

csrf = CSRFProtect(app)

Talisman(app, content_security_policy=None)

socketio = SocketIO(app)

thresholds = {
    'temperature_min': 0.0,
    'temperature_max': 40.0,
    'humidity_min': 10.0,
    'humidity_max': 90.0,
    'pressure_min': 970.0,
    'pressure_max': 1030.0
}

def initialize_database():
    """Ensure the 'readings' table exists in environment.db."""
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                pressure REAL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error initializing database:", e)

initialize_database()

def get_latest_reading():
    """Retrieve the latest sensor reading from environment.db."""
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return {
                'timestamp': row[0],
                'temperature': row[1],
                'humidity': row[2],
                'pressure': row[3]
            }
        else:
            return None
    except Exception as e:
        print("Error retrieving latest reading:", e)
        return None

def background_thread():
    """Background thread that emits sensor_update events via Socket.IO every 5 seconds."""
    while True:
        reading = get_latest_reading()
        if reading:
            warnings = {}
            if reading['temperature'] < thresholds['temperature_min'] or reading['temperature'] > thresholds['temperature_max']:
                warnings['temperature'] = True
            if reading['humidity'] < thresholds['humidity_min'] or reading['humidity'] > thresholds['humidity_max']:
                warnings['humidity'] = True
            if reading['pressure'] < thresholds['pressure_min'] or reading['pressure'] > thresholds['pressure_max']:
                warnings['pressure'] = True
            reading['warnings'] = warnings

            socketio.emit('sensor_update', reading)
        time.sleep(5)

thread = threading.Thread(target=background_thread)
thread.daemon = True
thread.start()

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html', thresholds=thresholds)

@app.route('/history')
def history():
    """Retrieve the 50 most recent sensor readings as JSON."""
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        data = []
        for row in reversed(rows):
            data.append({
                'timestamp': row[0],
                'temperature': row[1],
                'humidity': row[2],
                'pressure': row[3]
            })
        return jsonify(data)
    except Exception as e:
        print("Error retrieving historical data:", e)
        return jsonify([])

@app.route('/update_thresholds', methods=['POST'])
@csrf.exempt  
def update_thresholds():
    """Update sensor threshold settings."""
    global thresholds
    data = request.get_json()
    for key in thresholds:
        if key in data:
            try:
                thresholds[key] = float(data[key])
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid value for ' + key}), 400
    return jsonify({'status': 'success', 'thresholds': thresholds})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

