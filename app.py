import os
import sqlite3
import threading
import time
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "your_secret_key")
csrf = CSRFProtect(app)
Talisman(app, content_security_policy=None)
socketio = SocketIO(app)
thresholds = {'temperature_min': 0.0, 'temperature_max': 40.0, 'humidity_min': 10.0, 'humidity_max': 90.0, 'pressure_min': 970.0, 'pressure_max': 1030.0}
def initialize_database():
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, temperature REAL, humidity REAL, pressure REAL)")
        conn.commit()
        conn.close()
        logging.info("Database initialized.")
    except Exception as e:
        logging.error("Database init error: %s", e)
initialize_database()
def get_latest_reading():
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return {'timestamp': row[0], 'temperature': row[1], 'humidity': row[2], 'pressure': row[3]}
        else:
            return None
    except Exception as e:
        logging.error("Error retrieving latest reading: %s", e)
        return None
def background_thread():
    while True:
        try:
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
            else:
                logging.warning("No latest reading.")
        except Exception as e:
            logging.error("Error in background thread: %s", e)
        time.sleep(5)
thread = threading.Thread(target=background_thread)
thread.daemon = True
thread.start()
@app.route('/')
def index():
    try:
        return render_template('index.html', thresholds=thresholds)
    except Exception as e:
        logging.error("Error rendering index: %s", e)
        return "Error rendering page", 500
@app.route('/history')
def history():
    try:
        conn = sqlite3.connect('environment.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        data = []
        for row in reversed(rows):
            data.append({'timestamp': row[0], 'temperature': row[1], 'humidity': row[2], 'pressure': row[3]})
        return jsonify(data)
    except Exception as e:
        logging.error("Error retrieving history: %s", e)
        return jsonify([])
@app.route('/update_thresholds', methods=['POST'])
@csrf.exempt
def update_thresholds():
    global thresholds
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        for key in thresholds:
            if key in data:
                thresholds[key] = float(data[key])
        logging.info("Thresholds updated: %s", thresholds)
        return jsonify({'status': 'success', 'thresholds': thresholds})
    except Exception as e:
        logging.error("Error updating thresholds: %s", e)
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.critical("Failed to start server: %s", e)
