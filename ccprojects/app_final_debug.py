from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import psutil, time, datetime, json, platform
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warnings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model for persistent warning logs
class WarningLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    warnings = db.Column(db.String, nullable=False)  # Stored as JSON string

# Create the database tables if they do not exist
with app.app_context():
    if not os.path.exists('warnings.db'):
        db.create_all()

def get_metrics(interface_name="wlan0"):
    metrics = {}
    # CPU
    metrics['cpu_percent'] = psutil.cpu_percent(interval=0.5)
    freq = psutil.cpu_freq()
    if freq:
        metrics['current_speed_ghz'] = round(freq.current / 1000, 2)
        metrics['min_speed_ghz'] = round(freq.min / 1000, 2)
        metrics['max_speed_ghz'] = round(freq.max / 1000, 2)
    else:
        metrics['current_speed_ghz'] = metrics['min_speed_ghz'] = metrics['max_speed_ghz'] = None
    metrics['cpu_name'] = platform.processor()
    metrics['physical_cores'] = psutil.cpu_count(logical=False)
    metrics['logical_cores'] = psutil.cpu_count(logical=True)
    
    # Memory
    mem = psutil.virtual_memory()
    metrics['memory_total'] = mem.total / (1024**3)
    metrics['memory_used'] = mem.used / (1024**3)
    metrics['memory_available'] = mem.available / (1024**3)
    metrics['memory_percent'] = mem.percent
    
    # Disk
    disk = psutil.disk_usage("/")
    metrics['disk_total'] = disk.total / (1024**3)
    metrics['disk_free'] = disk.free / (1024**3)
    metrics['disk_percent'] = disk.percent
    
    # Battery
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    if battery:
        metrics['battery_percent'] = battery.percent
        metrics['power_plugged'] = battery.power_plugged
    else:
        metrics['battery_percent'] = None
        metrics['power_plugged'] = None
    
    # Temperature (CPU)
    temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    cpu_temp = None
    for sensor, entries in temps.items():
        for entry in entries:
            if cpu_temp is None or entry.current > cpu_temp:
                cpu_temp = entry.current
    metrics['cpu_temp'] = cpu_temp
    
    # Wi-Fi (simplified, using overall network stats for now)
    net_all = psutil.net_io_counters(pernic=True)
    wlan = net_all.get(interface_name)  # Use the configurable interface name
    if wlan:
        metrics['send_kbps'] = wlan.bytes_sent / 1024  # Convert bytes to kilobytes
        metrics['recv_kbps'] = wlan.bytes_recv / 1024  # Convert bytes to kilobytes
        metrics['adapter_name'] = interface_name
        metrics['ssid'] = "Example_SSID"
        metrics['connection_type'] = "802.11ac"
        metrics['ip4'] = "192.168.1.100"
    else:
        metrics['send_kbps'] = metrics['recv_kbps'] = 0
        metrics['adapter_name'] = "N/A"
        metrics['ssid'] = metrics['connection_type'] = metrics['ip4'] = "N/A"
    
    # Log the metrics for debugging
    print("Metrics collected:", metrics)
    
    # Check for warnings and log them
    warnings = []
    if metrics['memory_percent'] > 90:
        warnings.append("Memory usage is very high!")
    if metrics['battery_percent'] is not None and not metrics['power_plugged'] and metrics['battery_percent'] < 20:
        warnings.append("Low battery!")
    if metrics['cpu_temp'] is not None and metrics['cpu_temp'] > 75:
        warnings.append("System overheating!")
    
    if warnings:
        log_entry = WarningLog(warnings=json.dumps(warnings))
        db.session.add(log_entry)
        db.session.commit()
    
    metrics['timestamp'] = int(time.time() * 1000)
    return metrics

@app.route("/")
def dashboard():
    initial_metrics = get_metrics()
    return render_template("dashboard.html", metrics=initial_metrics)

@app.route("/data")
def data():
    return jsonify(get_metrics())

@app.route("/warnings")
def warnings():
    # Optional filtering via query parameters (start and end in ISO format)
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    query = WarningLog.query
    if start_str:
        try:
            start_dt = datetime.datetime.fromisoformat(start_str)
            query = query.filter(WarningLog.timestamp >= start_dt)
        except Exception:
            pass
    if end_str:
        try:
            end_dt = datetime.datetime.fromisoformat(end_str)
            query = query.filter(WarningLog.timestamp <= end_dt)
        except Exception:
            pass
    logs = query.order_by(WarningLog.timestamp.desc()).all()
    result = []
    for log in logs:
        result.append({
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "warnings": json.loads(log.warnings)
        })
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
