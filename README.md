# AI-Powered IoT Visitor Detection and Digital Logging System

## Overview
This project is a smart hostel security system that uses AI and IoT technologies for automated visitor detection and digital logging. The system uses ESP32-CAM for image capture and OpenCV with CompreFace for face recognition.

Authorized users are granted access automatically, while unknown visitors must complete OTP verification. All visitor activities are stored digitally and monitored through a Streamlit dashboard.

## Features
- Face recognition using OpenCV and CompreFace
- ESP32-CAM based image capture
- OTP verification for unknown visitors
- Digital visitor logging
- Email notifications
- Streamlit dashboard for monitoring
- Automated door access control

## Technologies Used

### Hardware
- ESP32-CAM
- Servo Motor
- LCD Display

### Software
- Python
- OpenCV
- CompreFace
- SQLite
- Streamlit
- Arduino IDE

## Project Structure

├── webcam_ard.py
├── dashboard.py
├── email_service_ard.py
├── visitor_db.py
├── visitor_logs.db
├── labels.json
├── lbph_model.xml
├── README.md
