import sqlite3
import datetime
import time
from sense_emu import SenseHat
sense = SenseHat()
conn = sqlite3.connect('environment.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, temperature REAL, humidity REAL, pressure REAL)")
conn.commit()
def read_sensor():
    temperature = sense.get_temperature()
    humidity = sense.get_humidity()
    pressure = sense.get_pressure()
    return temperature, humidity, pressure
def log_reading():
    temperature, humidity, pressure = read_sensor()
    cursor.execute("INSERT INTO readings (temperature, humidity, pressure) VALUES (?, ?, ?)", (temperature, humidity, pressure))
    conn.commit()
while True:
    log_reading()
    time.sleep(5)
