from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import sqlite3
import threading
import time
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)
thresholds = {'temperature_min': 0.0, 'temperature_max': 40.0, 'humidity_min': 10.0, 'humidity_max': 90.0, 'pressure_min': 970.0, 'pressure_max': 1030.0}
def get_latest_reading():
    conn = sqlite3.connect('environment.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {'timestamp': row[0], 'temperature': row[1], 'humidity': row[2], 'pressure': row[3]}
    else:
        return None
def background_thread():
    while True:
        reading = get_latest_reading()
        if reading:
            socketio.emit('sensor_update', reading)
        time.sleep(5)
thread = threading.Thread(target=background_thread)
thread.daemon = True
thread.start()
@app.route('/')
def index():
    return render_template('index.html', thresholds=thresholds)
@app.route('/history')
def history():
    conn = sqlite3.connect('environment.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, temperature, humidity, pressure FROM readings ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    data = []
    for row in reversed(rows):
        data.append({'timestamp': row[0], 'temperature': row[1], 'humidity': row[2], 'pressure': row[3]})
    return jsonify(data)
@app.route('/update_thresholds', methods=['POST'])
def update_thresholds():
    global thresholds
    data = request.get_json()
    for key in thresholds:
        if key in data:
            thresholds[key] = float(data[key])
    return jsonify({'status': 'success', 'thresholds': thresholds})
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
