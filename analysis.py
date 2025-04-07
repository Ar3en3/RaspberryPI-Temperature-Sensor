import sqlite3
import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

def get_readings(limit=50):

    conn = sqlite3.connect('environment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature FROM readings ORDER BY timestamp ASC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def plot_historical_temperature():
    data = get_readings(50)
    if not data:
        print("No data found in the database.")
        return

    timestamps = [datetime.datetime.fromisoformat(row[0]) for row in data]
    temperatures = [row[1] for row in data]

    times_numeric = mdates.date2num(timestamps)

    m, b = np.polyfit(times_numeric, temperatures, 1)
    regression_line = m * np.array(times_numeric) + b

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, temperatures, 'bo-', label='Temperature')

    plt.plot(timestamps, regression_line, 'r--', label='Trend Line')

    plt.gcf().autofmt_xdate()
    plt.xlabel('Time')
    plt.ylabel('Temperature (°C)')
    plt.title('Historical Temperature Data with Linear Trend')
    plt.legend()

    plt.show()

if __name__ == "__main__":
    plot_historical_temperature()
