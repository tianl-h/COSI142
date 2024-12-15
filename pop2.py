import json
from datetime import datetime
import random
import threading
from gpiozero import LED, Button
import time
import cv2
from picamera2 import Picamera2
import smbus2
import os
import time
import smbus2
import webbrowser
import subprocess
import socket

class LCD1602(object):
    # commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # flags for display entry mode
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # flags for display on/off control
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00

    # flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    def __init__(self, bus, lines, dotsize, lcd_addr=0x3e):
        self.bus = bus  # SMBus instance
        self.lcd_address = lcd_addr
        self.line = lines
        self.currline = 0
        self.display_control = self.LCD_DISPLAYON
        if lines > 1:
            self.display_control |= self.LCD_2LINE
        if dotsize != 0 & lines == 1:
            self.display_control |= self.LCD_5x10DOTS

        time.sleep(0.05)  # Wait for LCD to power up

        # Send function set command sequence
        self.command(self.LCD_FUNCTIONSET | self.display_control)
        time.sleep(0.0045)  # Wait more than 4.1ms

        # Second attempt
        self.command(self.LCD_FUNCTIONSET | self.display_control)
        time.sleep(0.00015)  # Wait more than 150us

        # Third attempt
        self.command(self.LCD_FUNCTIONSET | self.display_control)

        # Set lines, font size, etc.
        self.command(self.LCD_FUNCTIONSET | self.display_control)

        # Turn the display on with no cursor or blinking
        self.display_mode = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
        self.display()

        # Clear the display
        self.clear()

        # Initialize to default text direction (left to right)
        self.display_mode = self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
        self.command(self.LCD_ENTRYMODESET | self.display_mode)

    def clear(self):
        self.command(self.LCD_CLEARDISPLAY)  # Clear display and reset cursor position
        time.sleep(0.002)  # This command takes a long time

    def home(self):
        self.command(self.LCD_RETURNHOME)  # Set cursor position to zero
        time.sleep(0.002)  # This command takes a long time

    def set_cursor(self, col, row):
        col = (col | 0x80) if row == 0 else (col | 0xc0)
        self.command(col)

    def no_display(self):
        self.display_control &= ~self.LCD_DISPLAYON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def display(self):
        self.display_control |= self.LCD_DISPLAYON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def no_cursor(self):
        self.display_control &= ~self.LCD_CURSORON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def cursor(self):
        self.display_control |= self.LCD_CURSORON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def no_blink(self):
        self.display_control &= ~self.LCD_BLINKON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def blink(self):
        self.display_control |= self.LCD_BLINKON
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def autoscroll(self):
        self.display_control |= self.LCD_ENTRYSHIFTINCREMENT
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def no_autoscroll(self):
        self.display_control &= ~self.LCD_ENTRYSHIFTINCREMENT
        self.command(self.LCD_DISPLAYCONTROL | self.display_control)

    def command(self, command):
        self.bus.write_byte_data(self.lcd_address, 0x80, command)  # Send command

    def write(self, char):
        self.bus.write_byte_data(self.lcd_address, 0x40, char)  # Send data

    def print(self, text):
        for char in text:
            self.write(ord(char))


class SleepQualityAnalyzer:
    def __init__(self, log_directory="sleep_logs"):
        self.motion_events = []
        self.sound_peaks = []
        self.monitoring_start_time = None
        self.monitoring_end_time = None
        self.lock = threading.Lock()
        self.log_directory = os.path.abspath(log_directory)
        
        # Ensure the log directory exists
        os.makedirs(self.log_directory, exist_ok=True)
        print(f"Log directory set to: {self.log_directory}")

    def start_monitoring(self):
        with self.lock:
            self.monitoring_start_time = datetime.now()
            self.motion_events.clear()
            self.sound_peaks.clear()
            print("Sleep quality monitoring started.")

    def stop_monitoring(self):
        with self.lock:
            self.monitoring_end_time = datetime.now()
            print("Sleep quality monitoring stopped.")

    def log_motion_event(self, start_time, end_time):
        with self.lock:
            duration = (end_time - start_time).total_seconds()
            self.motion_events.append({"start": start_time, "end": end_time, "duration": duration})
            print(f"Motion event logged from {start_time} to {end_time}, duration: {duration:.2f} seconds")

    def log_sound_peak(self, timestamp):
        with self.lock:
            self.sound_peaks.append(timestamp)
            print(f"Sound peak logged at {timestamp}")

    def calculate_sleep_score(self):
        with self.lock:
            if not self.monitoring_start_time or not self.monitoring_end_time:
                return None

            # Calculate total monitoring duration in hours
            total_duration = (self.monitoring_end_time - self.monitoring_start_time).total_seconds() / 3600  # in hours

            if total_duration == 0:
                return 50  # Default to 50 if the total duration is too short to evaluate

            # 1. Calculate motion score
            total_motion_duration = sum(event["duration"] for event in self.motion_events) / 3600  # in hours
            motion_percentage = (total_motion_duration / total_duration) * 100
            motion_penalty = min(motion_percentage * 1.5, 100)  # Adjusted to 1.5 points deduction per percentage of motion
            motion_score = max(100 - motion_penalty, 10)  # Ensure a minimum motion score of 10

            # 2. Calculate sound score
            sound_frequency = len(self.sound_peaks) / total_duration  # Sound peaks per hour
            sound_penalty = min(sound_frequency * 5, 100)  # Adjusted to 5 points deduction per sound peak per hour
            sound_score = max(100 - sound_penalty, 10)  # Ensure a minimum sound score of 10

            # 3. Calculate overall sleep score
            # Adjust weightings dynamically if thereâ€™s too much movement or noise
            if motion_percentage > 50:
                motion_weight = 0.7  # Increase weight of motion if movement is very high
                sound_weight = 0.3
            elif sound_frequency > 20:
                motion_weight = 0.4  # Increase weight of sound if noise is very high
                sound_weight = 0.6
            else:
                motion_weight = 0.6  # Default weightings
                sound_weight = 0.4

            sleep_score = (motion_score * motion_weight) + (sound_score * sound_weight)

            # Ensure a minimum sleep score to avoid 0
            sleep_score = min(max(sleep_score, 15), 100)  # Minimum sleep score is 15

            return round(sleep_score, 2)

           

    def generate_sleep_report(self):
        sleep_score = self.calculate_sleep_score()
        if sleep_score is None:
            return "No monitoring data available."

        total_duration = (self.monitoring_end_time - self.monitoring_start_time).total_seconds() / 3600  # in hours
        total_motion_duration = sum(event["duration"] for event in self.motion_events) / 3600  # in hours
        motion_percentage = (total_motion_duration / total_duration) * 100 if total_duration > 0 else 0

        report = {
            "sleep_score": sleep_score,
            "monitoring_duration": f"{total_duration:.2f} hours",
            "motion_events": len(self.motion_events),
            "total_motion_duration": f"{total_motion_duration:.2f} hours",
            "motion_percentage": f"{motion_percentage:.2f}%",
            "sound_peaks": len(self.sound_peaks),
            "sound_peaks_per_hour": round(len(self.sound_peaks) / total_duration, 2) if total_duration > 0 else 0
        }

        return report

    def save_log(self):
        with self.lock:
            if not self.monitoring_end_time:
                self.monitoring_end_time = datetime.now()
            
            # Generate filename based on start and end time
            start_time_str = self.monitoring_start_time.strftime("%Y%m%d_%H%M%S")
            end_time_str = self.monitoring_end_time.strftime("%Y%m%d_%H%M%S")
            filename = f"sleep_log_{start_time_str}_to_{end_time_str}.json"
            filepath = os.path.join(self.log_directory, filename)

            log_data = {
                "start_time": self.monitoring_start_time.isoformat(),
                "end_time": self.monitoring_end_time.isoformat(),
                "motion_events": [
                    {"start": event["start"].isoformat(), "end": event["end"].isoformat(), "duration": event["duration"]}
                    for event in self.motion_events
                ],
                "sound_peaks": [peak.isoformat() for peak in self.sound_peaks]
            }
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return filepath

    def append_report_to_log(self, filepath):
        report = self.generate_sleep_report()
        with open(filepath, 'r+') as f:
            data = json.load(f)
            data["sleep_report"] = report
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        return report

class SoundMonitor(threading.Thread):
    def __init__(self, sound_sensor_pin=27, threshold=5, detection_window=1.0, cooldown=0.1, analyzer=None):
        super().__init__()
        self.sound_sensor_pin = sound_sensor_pin
        self.sound_sensor = None
        self.threshold = threshold
        self.detection_window = detection_window
        self.cooldown = cooldown
        self.analyzer = analyzer
        self.running = False
        self.last_peak_time = 0
        self.detections_in_window = 0
        self.window_start_time = time.time()

    def run(self):
        self.sound_sensor = Button(self.sound_sensor_pin, pull_up=False)
        self.running = True
        print("Sound monitoring started.")
        while self.running:
            if self.sound_sensor.is_pressed:
                self.sound_detected()
            time.sleep(0.001)  # Increased responsiveness

    def sound_detected(self):
        current_time = time.time()
        
        # Reset the window if it has expired
        if current_time - self.window_start_time > self.detection_window:
            self.detections_in_window = 0
            self.window_start_time = current_time

        self.detections_in_window += 1

        # Check if we've exceeded the threshold within the detection window
        if self.detections_in_window >= self.threshold:
            self.peak_detected()
            self.detections_in_window = 0  # Reset after detecting a peak

    def peak_detected(self):
        current_time = time.time()
        if current_time - self.last_peak_time < self.cooldown:
            return  # Skip if we're still in the cooldown period

        self.last_peak_time = current_time
        print("Peak detected!")
        
        # Log each peak as it occurs
        if self.analyzer:
            self.analyzer.log_sound_peak(datetime.now())

    def stop(self):
        self.running = False
        if self.sound_sensor:
            self.sound_sensor.close()
        print("Sound monitoring stopped.")

class InfraredCameraMonitor(threading.Thread):
    def __init__(self, resolution=(640, 480), framerate=30, analyzer=None):
        super().__init__()
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(main={"size": resolution, "format": "RGB888"})
        self.camera.configure(config)
        self.camera.set_controls({"FrameDurationLimits": (int(1/framerate*1000000), int(1/framerate*1000000))})
        self.prev_frame = None
        self.motion_threshold = 1000
        self.analyzer = analyzer
        self.running = False
        self.motion_ongoing = False
        self.motion_start_time = None
        self.motion_cooldown = 3  # Time in seconds to wait before considering a new motion event

    def run(self):
        self.camera.start()
        self.running = True
        time.sleep(2)
        print("Camera monitoring started.")
        while self.running:
            image = self.camera.capture_array()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if self.prev_frame is None:
                self.prev_frame = gray
                continue

            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 40, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) > self.motion_threshold:
                    motion_detected = True
                    break

            current_time = time.time()

            if motion_detected and not self.motion_ongoing:
                # Start of a new motion event
                self.motion_ongoing = True
                self.motion_start_time = current_time
                print("Motion started!")
            elif not motion_detected and self.motion_ongoing:
                # Potential end of motion event
                if current_time - self.motion_start_time > self.motion_cooldown:
                    # Motion has stopped for longer than the cooldown period
                    self.motion_ongoing = False
                    motion_end_time = current_time
                    print(f"Motion ended! Duration: {motion_end_time - self.motion_start_time:.2f} seconds")
                    if self.analyzer:
                        self.analyzer.log_motion_event(
                            datetime.fromtimestamp(self.motion_start_time),
                            datetime.fromtimestamp(motion_end_time)
                        )

            self.prev_frame = gray
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.camera.close()
        print("Camera monitoring stopped.")

class LCDButtonInterface:
    def __init__(self, lcd, button, analyzer):
        self.lcd = lcd
        self.button = button
        self.analyzer = analyzer
        self.sound_monitor = None
        self.camera_monitor = None
        self.monitoring = False
        self.button.when_pressed = self.toggle_monitoring
        self.idle_timer = None

    def toggle_monitoring(self):
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def display_message(self, line1, line2=""):
        self.lcd.clear()
        self.lcd.print(line1)
        if line2:
            self.lcd.set_cursor(0, 1)
            self.lcd.print(line2)

    def start_monitoring(self):
        if not self.monitoring:
            self.cancel_idle_timer()
            self.display_message("Starting", "Monitoring...")
            time.sleep(1)

            self.analyzer.start_monitoring()

            self.display_message("Initializing", "Sound Monitor")
            self.sound_monitor = SoundMonitor(analyzer=self.analyzer)
            self.sound_monitor.start()
            time.sleep(1)

            self.display_message("Initializing", "Camera Monitor")
            self.camera_monitor = InfraredCameraMonitor(analyzer=self.analyzer)
            self.camera_monitor.start()
            time.sleep(1)

            self.display_message("Monitoring", "Active")
            self.monitoring = True
            print("Monitoring started.")
        else:
            self.display_message("Already", "Monitoring")
            time.sleep(2)
            self.display_message("Monitoring", "Active")

    def stop_monitoring(self):
        if self.monitoring:
            self.display_message("Stopping", "Monitoring...")
            time.sleep(1)

            if self.sound_monitor:
                self.sound_monitor.stop()
                self.sound_monitor.join()
                self.sound_monitor = None

            if self.camera_monitor:
                self.camera_monitor.stop()
                self.camera_monitor.join()
                self.camera_monitor = None

            self.analyzer.stop_monitoring()

            self.display_message("Saving Log", "Please Wait...")
            log_file = self.analyzer.save_log()
            time.sleep(1)

            self.display_message("Generating", "Sleep Report")
            report = self.analyzer.append_report_to_log(log_file)
            time.sleep(2)

            if isinstance(report, dict):
                sleep_score = report.get("sleep_score", 0)
                self.display_message(f"Sleep Score:", f"{sleep_score:.2f}")
                time.sleep(3)
            
                # Launch web interface after showing sleep score
                self.display_message("Opening", "Web Report...")
                self.launch_web_interface()
            else:
                self.display_message("Error:", "No Valid Report")
                time.sleep(1)

            self.monitoring = False
            print("Monitoring stopped and report saved.")
            self.schedule_idle_message()
        else:
            self.display_message("Not Currently", "Monitoring")
            time.sleep(2)
            self.show_idle_message()

    def show_idle_message(self):
        self.display_message("Press Button", "to Start/Stop")

    def schedule_idle_message(self):
        self.cancel_idle_timer()
        self.idle_timer = threading.Timer(5.0, self.show_idle_message)
        self.idle_timer.start()

    def cancel_idle_timer(self):
        if self.idle_timer:
            self.idle_timer.cancel()
            self.idle_timer = None

    def cleanup(self):
        self.cancel_idle_timer()
        if self.monitoring:
            self.stop_monitoring()
        if self.button:
            self.button.close()
        if self.lcd:
            self.display_message("System", "Shutting Down")
            time.sleep(2)
            self.lcd.clear()

    def stop_monitoring(self):
        if self.monitoring:
            self.display_message("Stopping", "Monitoring...")
            time.sleep(1)

            if self.sound_monitor:
                self.sound_monitor.stop()
                self.sound_monitor.join()
                self.sound_monitor = None

            if self.camera_monitor:
                self.camera_monitor.stop()
                self.camera_monitor.join()
                self.camera_monitor = None

            self.analyzer.stop_monitoring()

            self.display_message("Saving Log", "Please Wait...")
            log_file = self.analyzer.save_log()
            time.sleep(1)

            self.display_message("Generating", "Sleep Report")
            report = self.analyzer.append_report_to_log(log_file)
            time.sleep(2)

            if isinstance(report, dict):
                sleep_score = report.get("sleep_score", 0)
                self.display_message(f"Sleep Score:", f"{sleep_score:.1f}")
                time.sleep(3)  # Show score for 3 seconds
                # self.display_message(f"Log Saved:", f"{os.path.basename(log_file)[:16]}")
                # time.sleep(3)  # Show log filename for 3 seconds
            else:
                self.display_message("Error:", "No Valid Report")
                time.sleep(1)

            # Launch web interface after saving the report
            self.display_message("Opening", "Web Report...")
            self.launch_web_interface()

            self.monitoring = False
            print("Monitoring stopped and report saved.")
            self.schedule_idle_message()
        else:
            self.display_message("Not Currently", "Monitoring")
            time.sleep(2)
            self.show_idle_message()

    def show_idle_message(self):
        self.display_message("Press Button", "to Start/Stop")

    def schedule_idle_message(self):
        self.cancel_idle_timer()
        self.idle_timer = threading.Timer(5.0, self.show_idle_message)
        self.idle_timer.start()

    def cancel_idle_timer(self):
        if self.idle_timer:
            self.idle_timer.cancel()
            self.idle_timer = None

    def cleanup(self):
        self.cancel_idle_timer()
        if self.monitoring:
            self.stop_monitoring()
        if self.button:
            self.button.close()
        if self.lcd:
            self.display_message("System", "Shutting Down")
            time.sleep(2)
            self.lcd.clear()

    def is_port_in_use(self, port):
        """Check if the given port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return False
            except socket.error:
                return True

    def launch_web_interface(self):
        try:
            # Only launch Flask if port 5000 is not in use
            if not self.is_port_in_use(5000):
                flask_process = subprocess.Popen(['python3', '/home/luna/Documents/app.py'])
                # Wait for the server to start
                time.sleep(2)
                self.display_message("Flask Server", "Started")
            else:
                self.display_message("Flask Server", "Already running")
            
            # Set up X11 display access
            display = ":0"  # Default display
            subprocess.run(['xhost', '+SI:localuser:root'])  # Allow root to access X server
            
            # Set the DISPLAY environment variable
            env = os.environ.copy()
            env['DISPLAY'] = display
            
            # Open Chromium with necessary environment and flags
            subprocess.Popen([
                'chromium-browser',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--new-window',
                'http://127.0.0.1:5000'
            ], env=env)
            
            self.display_message("Web Interface", "Launched")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error launching web interface: {e}")
            self.display_message("Error Launch", "Web Interface")
            time.sleep(2)

def main():
    log_directory = "/home/luna/Documents/sleep_logs"
    bus = smbus2.SMBus(1)
    lcd = LCD1602(bus, lines=2, dotsize=0)
    analyzer = SleepQualityAnalyzer(log_directory=log_directory)
    control_button = Button(25)

    lcd_interface = LCDButtonInterface(lcd, control_button, analyzer)

    print("Sleep monitoring system ready. Press the button to start/stop monitoring.")
    lcd_interface.show_idle_message()  # Display the initial "Press Button" message
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting program.")
        lcd_interface.cleanup()

if __name__ == "__main__":
    main()