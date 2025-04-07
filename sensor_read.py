import sqlite3
import datetime
import time
from sense_emu import SenseHat  

sense = SenseHat()

conn = sqlite3.connect('environment.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity REAL,
    pressure REAL
)
''')
conn.commit()

def read_sensor():
    """
    Reads sensor data from the Sense HAT (or emulator).
    Falls back to default values if sensor reading fails.
    Returns a tuple of (temperature, humidity, pressure).
    """
    try:
        temperature = sense.get_temperature()
    except Exception as e:
        print("Temperature error:", e)
        temperature = 25.0  

    try:
        humidity = sense.get_humidity()
    except Exception as e:
        print("Humidity error:", e)
        humidity = 50.0  

    try:
        pressure = sense.get_pressure()
    except Exception as e:
        print("Pressure error:", e)
        pressure = 1013.25  

    return temperature, humidity, pressure

def log_reading():
    """
    Reads sensor data and stores the values in the 'readings' table.
    """
    temperature, humidity, pressure = read_sensor()
  
    cursor.execute(
        "INSERT INTO readings (temperature, humidity, pressure) VALUES (?, ?, ?)",
        (temperature, humidity, pressure)
    )
    conn.commit()
    print("Logged reading at", datetime.datetime.now(),
          "- Temperature:", temperature,
          "Humidity:", humidity,
          "Pressure:", pressure)

if __name__ == "__main__":
    print("Starting sensor logging. Press Ctrl+C to stop.")
    try:
        while True:
            log_reading()
            time.sleep(5)  
    except KeyboardInterrupt:
        print("Stopping sensor logging.")
    finally:
        conn.close()

