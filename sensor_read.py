import sqlite3
import datetime
import time
import random
from sense_emu import SenseHat
sense = SenseHat()
conn = sqlite3.connect('environment.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, temperature REAL, humidity REAL, pressure REAL)")
conn.commit()
def read_sensor():
    try:
        temperature = sense.get_temperature()
    except:
        temperature = 25.0 + random.uniform(-3,3)
    try:
        humidity = sense.get_humidity()
    except:
        humidity = 50.0 + random.uniform(-5,5)
    try:
        pressure = sense.get_pressure()
    except:
        pressure = 1013.25 + random.uniform(-10,10)
    return temperature, humidity, pressure
def update_led(temperature):
    if temperature > 30:
        color = (255,0,0)
    elif temperature < 20:
        color = (0,0,255)
    else:
        color = (0,255,0)
    pixels = [color]*64
    sense.set_pixels(pixels)
def log_reading():
    temperature, humidity, pressure = read_sensor()
    update_led(temperature)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO readings (timestamp, temperature, humidity, pressure) VALUES (?, ?, ?, ?)", (timestamp, temperature, humidity, pressure))
    conn.commit()
    print(timestamp, temperature, humidity, pressure)
if __name__ == "__main__":
    try:
        while True:
            log_reading()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        conn.close()
