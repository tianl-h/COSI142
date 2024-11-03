# COSI142

# Sleep Quality Monitoring System

A Raspberry Pi-based system for monitoring sleep quality using motion detection and sound sensors, providing real-time feedback through an LCD display and a web interface.

## Overview

This project uses a Raspberry Pi 5 to monitor sleep quality by detecting motion through an infrared camera and snoring events through a sound sensor. The system calculates a sleep score based on these inputs and displays it on an LCD screen. All data is logged and can be accessed through a web interface.

## Features

- **Motion Detection**: Uses infrared camera for accurate motion tracking even in darkness
- **Sound Monitoring**: Detects and logs snoring events
- **Real-time Display**: Shows sleep quality score on LCD display
- **Web Interface**: Access detailed sleep metrics and historical data
- **Easy Control**: Simple button interface to start/stop monitoring
- **Data Logging**: Comprehensive JSON logs of all sleep sessions

## Hardware Requirements

- Raspberry Pi 5
- Infrared Camera (compatible with Raspberry Pi)
- Sound Sensor
- LCD1602 Display (I2C interface)
- Push Button
- Necessary cables and power supply

## Contributors

- Tianling Hou (tianlinghou@brandeis.edu)
- Bing Han (binghan@brandeis.edu)
- Feifan He (feifanhe@brandeis.edu)
