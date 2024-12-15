# app.py
import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template
import psutil
import subprocess

app = Flask(__name__)

# Path to the location of your JSON files
JSON_FOLDER_PATH = os.path.expanduser('/home/luna/Documents/sleep_logs')

def get_datetime_from_filename(filename):
    """Extract and parse datetime from the filename."""
    parts = filename.split('_')
    if len(parts) >= 4:
        date_str = parts[2]  # The date part (20241102)
        time_str = parts[3].split('.')[0]  # The time part (143305), remove .json
        datetime_str = date_str + time_str
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
    return None

def format_datetime_display(dt):
    """Format datetime for display in the UI."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return None

def load_sorted_json_files(reverse_chronological=True):
    """Load and sort sleep monitoring session files by datetime."""
    files = [f for f in os.listdir(JSON_FOLDER_PATH) if f.startswith('sleep_log_') and f.endswith('.json')]
    files.sort(key=get_datetime_from_filename, reverse=reverse_chronological)
    return files

def process_sleep_data(data, filename):
    """Process sleep monitoring data and format it for display."""
    sleep_report = data.get('sleep_report', {})
    session_datetime = get_datetime_from_filename(filename)
    
    return {
        'session_datetime': format_datetime_display(session_datetime),
        'sleep_quality_score': sleep_report.get('sleep_score', 0),
        'acoustic_disturbances': len(data.get('sound_peaks', [])),
        'movement_activity': len(data.get('motion_events', [])),
        'monitoring_duration': sleep_report.get('monitoring_duration', '0'),
        'motion_percentage': sleep_report.get('motion_percentage', '0%'),
        'acoustic_frequency': sleep_report.get('sound_peaks_per_hour', 0)
    }

def fetch_recent_sessions(n):
    """Fetch the most recent n sleep monitoring sessions."""
    # Get files in reverse chronological order for selecting most recent n files
    files = load_sorted_json_files(reverse_chronological=True)
    selected_files = files[:n]
    sleep_data = []
    
    # Process the selected files in chronological order (oldest to newest)
    for file in reversed(selected_files):
        file_path = os.path.join(JSON_FOLDER_PATH, file)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                sleep_data.append(process_sleep_data(data, file))
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file}")
        except Exception as e:
            print(f"Error processing file {file}: {str(e)}")
    
    return sleep_data

@app.route('/')
def index():
    """Render the main dashboard with the latest sleep monitoring data."""
    # For latest data, still get the most recent
    latest_data = fetch_recent_sessions(1)[-1] if fetch_recent_sessions(1) else {}
    return render_template('index.html', latest_data=latest_data)

@app.route('/kill-monitoring', methods=['POST'])
def kill_monitoring():
    """Kill the current pop2.py process."""
    killed = False
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.cmdline()  # Get the full command line
                # Print for debugging
                print(f"Found process: {cmdline}")
                if any('pop2.py' in cmd for cmd in cmdline):
                    print(f"Killing process: {proc.pid}")
                    proc.kill()  
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print(f"Error checking process: {e}")
                continue
        
        return jsonify({
            "status": "success" if killed else "no_process_found",
            "message": "Process killed" if killed else "No pop2.py process found"
        })
    except Exception as e:
        print(f"Error in kill_monitoring: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/kill-monitoring', methods=['POST'])
# def kill_monitoring():
#     """Kill the current pop2.py process."""
#     killed = False
#     for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
#         try:
#             if proc.info['cmdline'] and 'python' in proc.info['cmdline'][0].lower() and 'pop2.py' in proc.info['cmdline'][1]:
#                 proc.terminate()
#                 killed = True
#                 break
#         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#             pass
#     return jsonify({"status": "success" if killed else "error"})

@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start a new monitoring session."""
    try:
        restart_script = '/home/luna/Documents/restart.sh'
        # Make sure the script is executable
        os.chmod(restart_script, 0o755)
        
        # Set up environment
        env = os.environ.copy()
        env['DISPLAY'] = ':0'
        env['XDG_RUNTIME_DIR'] = '/run/user/1000'
        
        # Start new monitoring session
        subprocess.Popen([
            'lxterminal',
            '-e',
            f'bash -c "{restart_script}; read -p \'Press Enter to close\'"'
        ], env=env, start_new_session=True)
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error starting monitoring: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/recent-sessions', methods=['GET'])
def get_recent_sessions():
    """API endpoint for recent sleep monitoring sessions (last 7)."""
    return jsonify(fetch_recent_sessions(7))

@app.route('/api/extended-analysis', methods=['GET'])
def get_extended_analysis():
    """API endpoint for extended sleep analysis (last 30 sessions)."""
    return jsonify(fetch_recent_sessions(30))

if __name__ == '__main__':
    app.run(debug=True)