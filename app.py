# app.py
import os
import json
from datetime import datetime
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Path to the location of your JSON files
JSON_FOLDER_PATH = os.path.expanduser('/Users/htl/Desktop/Brandeis/142/web/sleep')
# JSON_FOLDER_PATH = os.path.expanduser('/home/luna/Documents/sleep_logs')

# Get the datetime (date and time) from the filename
def get_datetime_from_filename(filename):
    date_str = filename.split('_')[2]  # Extract date from filename
    time_str = filename.split('_')[3]  # Extract start time from filename
    datetime_str = date_str + time_str  # Combine date and time into one string
    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")  # Parse both date and time


# Load all files and sort them by date and time
def load_sorted_json_files():
    files = [f for f in os.listdir(JSON_FOLDER_PATH) if f.startswith('sleep_log_') and f.endswith('.json')]
    files.sort(key=get_datetime_from_filename, reverse=True)  # Sort files by datetime, most recent first
    return files


# Calculate sleep score and extract relevant data
# def process_sleep_data(data, filename):
#     sleep_report = data.get('Sleep report', [{}])[0]
#     date = get_date_from_filename(filename).strftime("%Y-%m-%d")
#     return {
#         'date': date,
#         'sleep_score': sleep_report.get('sleep_score', 0),
#         'noise_events': len(data.get('sound_peaks', [])),
#         'movement_events': len(data.get('motion_events', [])),
#         'monitoring_duration': sleep_report.get('monitoring_duration', '0')
#     }

def process_sleep_data(data, filename=None):
    sleep_report = data.get('sleep_report', {})  # Use 'sleep_report'
    return {
        'date': data['start_time'].split('T')[0],
        'sleep_score': sleep_report.get('sleep_score', 0),
        'noise_events': len(data.get('sound_peaks', [])),
        'movement_events': len(data.get('motion_events', [])),
        'monitoring_duration': sleep_report.get('monitoring_duration', '0')
    }

# Fetch the last N days of sleep data
def fetch_last_n_days_data(n):
    files = load_sorted_json_files()
    selected_files = files[:n]  # Select the last N files
    sleep_data = []
    
    for file in selected_files:
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
    latest_data = fetch_last_n_days_data(1)[0] if fetch_last_n_days_data(1) else {}
    return render_template('index.html', latest_data=latest_data)

@app.route('/api/last7days', methods=['GET'])
def get_last_7_days_data():
    return jsonify(fetch_last_n_days_data(7))

@app.route('/api/last30days', methods=['GET'])
def get_last_30_days_data():
    return jsonify(fetch_last_n_days_data(30))

if __name__ == '__main__':
    app.run(debug=True)