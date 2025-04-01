System Monitor Dashboard Documentation

Team Members
2409016 - Stefan Mathias
2409017 - Aston Fernandes
2409025 - Joshua Pinto
2409033 - Kaif Ansari
GitHub Link : 
Overview
The System Monitor Dashboard is a Linux-specific monitoring tool built using Python Flask, psutil, and Chart.js. It provides real-time system performance metrics and interactive visualizations with a futuristic teal theme. The dashboard features three main tabs:

Dashboard: Displays a digital gauge and basic real-time metrics (CPU, Memory, Disk, Battery, Temperature).


Usage Analysis: Offers detailed charts and metrics for CPU, RAM, Wi-Fi, Battery, and Temperature with interactive visualizations.


Warnings: Shows current warnings (e.g., high memory usage, low battery, overheating) and a log of past warning events.

Features
Real-Time Monitoring:
System metrics are fetched every 2 seconds via a /data endpoint, using the psutil library.


Interactive Visualizations:
Charts are rendered with Chart.js and use the streaming plugin for live data updates.
Usage Analysis includes line charts for CPU, RAM, and Wi-Fi data, and bar charts for Battery and Temperature.


Warning System:
The backend logs warnings if metrics exceed thresholds (e.g., memory usage > 90%, battery < 20%, CPU temperature > 75°C) using Flask-SQLAlchemy.
The Warnings tab displays both current warnings and historical logs.

Requirements
Operating System: Linux


Python 3.x


Dependencies:
Flask
Flask-SQLAlchemy
psutil
Chart.js
Chartjs-plugin-streaming 

File Structure
ccproject/                           # Main project folder
├── app.py                       # Flask backend collecting system metrics and serving endpoints
├── venv/                         # Python virtual environment (auto-generated)
└── templates	       # Templates folder
    └── dashboard.html     # Frontend HTML with interactive charts and animations

Installation and Setup
1. Create the Project Folder:


cd ~/Desktop
mkdir ccproject
cd ccproject


2. Set Up Virtual Environment:


python3 -m venv venv
source venv/bin/activate


3. Install Python Dependencies:


pip install flask flask_sqlalchemy psutil


4. Create File Structure:
In the ccproject folder, create the file app.py.


5. Create a folder named templates:


mkdir templates

Inside the templates folder, create dashboard.html.


6. Add the Code:
app.py:  (see Appendix A).


dashboard.html:  (see Appendix B).


7. Run the Application:

python3 app_final_debug_v4.py



Appendix:

Appendix A(app.py code)

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

def get_metrics(interface_name="Wi-Fi"):  # Updated interface name
    metrics = {}
    # CPU
    metrics['cpu_percent'] = round(psutil.cpu_percent(interval=0.5), 2)
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
    metrics['memory_total'] = round(mem.total / (1024**3), 2)
    metrics['memory_used'] = round(mem.used / (1024**3), 2)
    metrics['memory_available'] = round(mem.available / (1024**3), 2)
    metrics['memory_percent'] = round(mem.percent, 2)
    
    # Disk
    disk = psutil.disk_usage("/")
    metrics['disk_total'] = round(disk.total / (1024**3), 2)
    metrics['disk_free'] = round(disk.free / (1024**3), 2)
    metrics['disk_percent'] = round(disk.percent, 2)
    
    # Battery
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    if battery:
        metrics['battery_percent'] = round(battery.percent, 2)
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
    wlan = net_all.get(interface_name)  # Use the updated interface name
    if wlan:
        metrics['send_kbps'] = round(wlan.bytes_sent / 1024, 2)  # Convert bytes to kilobytes
        metrics['recv_kbps'] = round(wlan.bytes_recv / 1024, 2)  # Convert bytes to kilobytes
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
    metrics = get_metrics()
    return jsonify(metrics)

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




Appendix B(dashboard.html)

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>System Monitor</title>
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&family=Orbitron:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-streaming@1.9.0/dist/chartjs-plugin-streaming.min.js"></script>
  <script>
    Chart.register(...Chart.registerables);
  </script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: 'Orbitron', 'Montserrat', sans-serif;
    }
    body {
      background: #0d0d0d;
      color: #fff;
      display: flex;
      min-height: 100vh;
      overflow-x: hidden;
    }
    a, button {
      font-family: 'Orbitron', 'Montserrat', sans-serif;
    }
    :root {
      --accent-color: #00c2c2;
    }
    .section {
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.5s ease, transform 0.5s ease;
      display: none;
    }
    .section.active {
      display: block;
      opacity: 1;
      transform: translateY(0);
    }
    .sidebar {
      width: 260px;
      background: linear-gradient(180deg, #141414, #1a1a1a);
      display: flex;
      flex-direction: column;
      padding: 20px 0;
      box-shadow: 2px 0 5px rgba(0,0,0,0.8);
    }
    .sidebar .logo {
      font-size: 1.4rem;
      font-weight: 600;
      color: var(--accent-color);
      text-align: center;
      margin-bottom: 40px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .menu {
      list-style: none;
    }
    .menu li {
      padding: 15px 40px;
      cursor: pointer;
      transition: background 0.3s, border-left 0.3s;
      border-left: 3px solid transparent;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 1rem;
    }
    .menu li:hover,
    .menu li.active {
      background: #222;
      border-left: 3px solid var(--accent-color);
    }
    .main-content {
      flex: 1;
      padding: 30px;
      background: linear-gradient(180deg, #101010, #181818);
      animation: fadeIn 1s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .glow-box {
      box-shadow: 0 0 10px rgba(0,194,194,0.3);
      border: 1px solid rgba(0,194,194,0.2);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glow-box:hover {
      transform: translateY(-5px);
      box-shadow: 0 0 15px rgba(0,194,194,0.5);
    }
    .card {
      margin-bottom: 30px;
      background: #1a1a1a;
      border: none;
      border-radius: 5px;
      box-shadow: 0 0 5px rgba(0,0,0,0.5);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
      transform: translateY(-5px);
      box-shadow: 0 0 15px rgba(0,0,0,0.7);
    }
    .card-body {
      background: linear-gradient(180deg, #1b1b1b, #212121);
      border-radius: 5px;
      box-shadow: inset 0 0 15px rgba(0,0,0,0.4);
      padding: 20px;
    }
    .card-title {
      color: var(--accent-color);
      letter-spacing: 0.5px;
      margin-bottom: 15px;
      font-size: 1.1rem;
    }
    .gauge-container {
      width: 300px;
      height: 300px;
      margin: 20px auto;
      position: relative;
      border: 6px solid var(--accent-color);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #1a1a1a;
      transition: box-shadow 0.3s ease;
    }
    .gauge-container:hover {
      box-shadow: 0 0 20px rgba(0,194,194,0.5);
    }
    .gauge-value {
      font-size: 3rem;
      font-weight: 600;
      letter-spacing: 0.5px;
    }
    .placeholder {
      color: lightgrey;
    }
    button:hover {
      transform: scale(1.1);
      background: var(--accent-color);
      color: #fff;
      transition: all 0.3s ease;
    }
    .mini-chart {
      max-height: 120px;
      margin: 10px 0;
    }
  </style>
</head>
<body>
  <div class="sidebar">
    <div class="logo">System Monitor</div>
    <ul class="menu">
      <li class="active" onclick="switchTab('dashboardSection', this)">Dashboard</li>
      <li onclick="switchTab('analysisSection', this)">Usage Analysis</li>
      <li onclick="switchTab('warningsSection', this)">Warnings</li>
    </ul>
  </div>
  
  <div class="main-content">
    <!-- Dashboard Section -->
    <div id="dashboardSection" class="section active">
      <h3>Dashboard</h3>
      <div class="gauge-container glow-box">
        <div class="gauge-value" id="gaugeValue">{{ metrics.cpu_percent }}%</div>
      </div>
      <div class="row">
        <div class="col-md-4">
          <div class="card glow-box">
            <div class="card-body">
              <h5 class="card-title">Memory Usage</h5>
              <canvas id="memoryMiniChart" class="mini-chart"></canvas>
              <p id="basicMemory">
                Total: <span class="placeholder">{{ metrics.memory_total | round(2) }} GB</span><br>
                Used: <span class="placeholder">{{ metrics.memory_used | round(2) }} GB</span><br>
                Utilization: <span class="placeholder">{{ metrics.memory_percent | round(2) }}%</span>
              </p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card glow-box">
            <div class="card-body">
              <h5 class="card-title">Disk Usage</h5>
              <canvas id="diskMiniChart" class="mini-chart"></canvas>
              <p id="basicDisk">
                Total: <span class="placeholder">{{ metrics.disk_total }} GB</span><br>
                Free: <span class="placeholder">{{ metrics.disk_free }} GB</span><br>
                Utilization: <span class="placeholder">{{ metrics.disk_percent }}%</span>
              </p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card glow-box">
            <div class="card-body">
              <h5 class="card-title">Battery & Temp</h5>
              <canvas id="batteryMiniChart" class="mini-chart" style="max-height: 100px;"></canvas>
              <canvas id="tempMiniChart" class="mini-chart" style="max-height: 60px;"></canvas>
              <p id="basicBattery">
                Battery: <span class="placeholder">{{ metrics.battery_percent }}%</span><br>
                Status: <span class="placeholder">{{ "Charging" if metrics.power_plugged else "Discharging" }}</span><br>
                Temp: <span id="tempValue" class="placeholder">{{ metrics.cpu_temp }}°C</span>
              </p>
            </div>
          </div>
        </div>
      </div>
      <div class="row mt-4">
        <canvas id="cpuChart" height="100"></canvas>
      </div>
    </div>

    <!-- Usage Analysis Section -->
    <div id="analysisSection" class="section">
      <h3 style="margin-bottom:20px; color:#ccc; text-transform:uppercase; letter-spacing:0.5px;">Usage Analysis</h3>
      <div class="card glow-box">
        <div class="card-body">
          <h5 class="card-title">CPU Analysis</h5>
          <div class="row">
            <div class="col-md-8">
              <canvas id="cpuUsageChart" height="150"></canvas>
            </div>
            <div class="col-md-4">
              <p id="cpuDetails">
                Name: <span class="placeholder">{{ metrics.cpu_name }}</span><br>
                Speed: <span class="placeholder">{{ metrics.current_speed_ghz }} GHz</span><br>
                Cores: <span class="placeholder">{{ metrics.physical_cores }}P/{{ metrics.logical_cores }}L</span><br>
                Utilization: <span class="placeholder">{{ metrics.cpu_percent }}%</span>
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card glow-box">
        <div class="card-body">
          <h5 class="card-title">RAM Analysis</h5>
          <div class="row">
            <div class="col-md-8">
              <canvas id="ramChartAnalysis" height="150"></canvas>
            </div>
            <div class="col-md-4">
              <p id="ramDetails">
                Total: <span class="placeholder">{{ metrics.memory_total }} GB</span><br>
                Available: <span class="placeholder">{{ metrics.memory_available }} GB</span><br>
                Utilization: <span class="placeholder">{{ metrics.memory_percent }}%</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="card glow-box">
        <div class="card-body">
          <h5 class="card-title">Network Analysis</h5>
          <div class="row">
            <div class="col-md-8">
              <canvas id="wifiChart" height="150"></canvas>
            </div>
            <div class="col-md-4">
              <p id="wifiDetails">
                Adapter: <span class="placeholder">{{ metrics.adapter_name }}</span><br>
                SSID: <span class="placeholder">{{ metrics.ssid }}</span><br>
                Protocol: <span class="placeholder">{{ metrics.connection_type }}</span><br>
                Sent: <span class="placeholder">{{ metrics.send_kbps }} KB/s</span><br>
                Received: <span class="placeholder">{{ metrics.recv_kbps }} KB/s</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Warnings Section -->
    <div id="warningsSection" class="section">
      <h3 style="margin-bottom:20px; color:#ccc; text-transform:uppercase; letter-spacing:0.5px;">Warnings</h3>
      <div class="card glow-box">
        <div class="card-body">
          <h5 class="card-title">Current Warnings</h5>
          <p id="warningText">No current warnings</p>
        </div>
      </div>
      <div class="card glow-box">
        <div class="card-body">
          <h5 class="card-title">Warning Logs</h5>
          <div id="warningLogs">Loading logs...</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Tab switching function
    function switchTab(sectionId, el) {
      document.querySelectorAll('.section').forEach(sec => {
        sec.classList.remove('active');
        sec.style.display = 'none';
      });
      document.querySelectorAll('.menu li').forEach(li => li.classList.remove('active'));
      
      const section = document.getElementById(sectionId);
      section.style.display = 'block';
      setTimeout(() => section.classList.add('active'), 10);
      el.classList.add('active');
    }

    // Mini Charts
    const memoryMiniChart = new Chart(document.getElementById('memoryMiniChart'), {
      type: 'doughnut',
      data: {
        labels: ['Used', 'Available'],
        datasets: [{
          data: [0, 100],
          backgroundColor: ['#00c2c2', '#2d2d2d']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } }
      }
    });

    const diskMiniChart = new Chart(document.getElementById('diskMiniChart'), {
      type: 'doughnut',
      data: {
        labels: ['Used', 'Free'],
        datasets: [{
          data: [0, 100],
          backgroundColor: ['#00c2c2', '#2d2d2d']
        }]
      },
      options: { /* Same as memoryMiniChart */ }
    });

    const batteryMiniChart = new Chart(document.getElementById('batteryMiniChart'), {
      type: 'doughnut',
      data: {
        labels: ['Remaining', 'Empty'],
        datasets: [{
          data: [0, 100],
          backgroundColor: ['#00c2c2', '#2d2d2d']
        }]
      },
      options: { /* Same as memoryMiniChart */ }
    });

    const tempMiniChart = new Chart(document.getElementById('tempMiniChart'), {
      type: 'bar',
      data: {
        labels: ['Temperature'],
        datasets: [{
          data: [0],
          backgroundColor: '#ff4545'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { display: false, beginAtZero: true },
          x: { display: false }
        }
      }
    });

    // Main Charts
    const cpuChart = new Chart(document.getElementById('cpuChart'), {
      type: 'line',
      data: {
        datasets: [{
          label: 'CPU Usage (%)',
          borderColor: '#00c2c2',
          backgroundColor: 'rgba(0,194,194,0.2)',
          fill: true,
          data: []
        }]
      },
      options: {
        plugins: { streaming: { frameRate: 30 } },
        scales: {
          x: { type: 'realtime', realtime: { delay: 2000, refresh: 2000 } },
          y: { beginAtZero: true, max: 100 }
        }
      }
    });

    const cpuUsageChart = new Chart(document.getElementById('cpuUsageChart'), {
      type: 'line',
      data: {
        datasets: [{
          label: 'CPU Usage (%)',
          borderColor: '#00c2c2',
          backgroundColor: 'rgba(0,194,194,0.2)',
          fill: true,
          data: []
        }]
      },
      options: { /* Same as main CPU chart */ }
    });

    const ramChartAnalysis = new Chart(document.getElementById('ramChartAnalysis'), {
      type: 'line',
      data: {
        datasets: [{
          label: 'RAM Usage (%)',
          borderColor: '#00c2c2',
          backgroundColor: 'rgba(0,194,194,0.2)',
          fill: true,
          data: []
        }]
      },
      options: { /* Same as main CPU chart */ }
    });

    const wifiChart = new Chart(document.getElementById('wifiChart'), {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'Sent (KB/s)',
            borderColor: '#ff6384',
            backgroundColor: 'rgba(255,99,132,0.2)',
            fill: true,
            data: []
          },
          {
            label: 'Received (KB/s)',
            borderColor: '#36a2eb',
            backgroundColor: 'rgba(54,162,235,0.2)',
            fill: true,
            data: []
          }
        ]
      },
      options: { /* Similar scaling options */ }
    });

    // Data Updates
    function updateAllCharts() {
      fetch('/data')
        .then(response => response.json())
        .then(data => {
          const now = Date.now();

          // Update mini charts
          memoryMiniChart.data.datasets[0].data = [data.memory_percent, 100 - data.memory_percent];
          memoryMiniChart.update();
          
          diskMiniChart.data.datasets[0].data = [data.disk_percent, 100 - data.disk_percent];
          diskMiniChart.update();
          
          batteryMiniChart.data.datasets[0].data = [data.battery_percent || 0, 100 - (data.battery_percent || 0)];
          batteryMiniChart.update();
          
          if(data.cpu_temp) {
            tempMiniChart.data.datasets[0].data = [data.cpu_temp];
            tempMiniChart.options.scales.y.max = data.cpu_temp + 10;
            tempMiniChart.update();
            document.getElementById('tempValue').textContent = `${data.cpu_temp}°C`;
          } else {
            document.getElementById('tempValue').textContent = 'N/A';
          }

          // Update main charts
          [cpuChart, cpuUsageChart].forEach(chart => {
            chart.data.datasets[0].data.push({ x: now, y: data.cpu_percent });
            chart.update('quiet');
          });

          ramChartAnalysis.data.datasets[0].data.push({ x: now, y: data.memory_percent });
          ramChartAnalysis.update('quiet');

          wifiChart.data.datasets[0].data.push({ x: now, y: data.send_kbps });
          wifiChart.data.datasets[1].data.push({ x: now, y: data.recv_kbps });
          wifiChart.update('quiet');

          // Update gauge
          document.getElementById('gaugeValue').textContent = `${data.cpu_percent}%`;

          // Update warnings
          updateWarnings(data);
        });
    }

    function updateWarnings(data) {
      const warnings = [];
      if(data.memory_percent > 90) warnings.push("Memory usage very high!");
      if(data.battery_percent !== null && !data.power_plugged && data.battery_percent < 20) {
        warnings.push("Low battery!");
      }
      if(data.cpu_temp !== null && data.cpu_temp > 75) {
        warnings.push("CPU overheating!");
      }
      document.getElementById('warningText').innerHTML = warnings.join('<br>') || 'No current warnings';
    }

    function updateWarningLogs() {
      fetch('/warnings')
        .then(response => response.json())
        .then(logs => {
          const logsHTML = logs.map(log => 
            `<p><strong>${log.timestamp}</strong>: ${log.warnings.join(', ')}</p>`
          ).join('');
          document.getElementById('warningLogs').innerHTML = logsHTML || '<p>No logs available</p>';
        });
    }

    // Start updates
    setInterval(updateAllCharts, 2000);
    setInterval(updateWarningLogs, 5000);
    updateAllCharts();
    updateWarningLogs();
  </script>
</body>
</html>



