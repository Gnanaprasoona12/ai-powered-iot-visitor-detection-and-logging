import cv2
import requests
import random
import time
import sqlite3
import os
import numpy as np
from datetime import datetime
from email_service_ard import EmailService
import risk_score
import visitor_db

# =========================
# INIT
# =========================
visitor_db.init_db()
email_service = EmailService()

ESP32_IP = "http://10.24.222.139"
STREAM_URL = 0  # Local webcam

print("Webcam System (OpenCV LBPH) running... Press ESC to exit")

# =========================
# LCD FUNCTION
# =========================
def send_lcd(msg):
    try:
        requests.get(f"{ESP32_IP}:8080/lcd", params={"msg": msg}, timeout=2)
    except:
        pass

ROOMS = {
    "101": [{"name": "Rishitha", "email": "rishithav19@gmail.com"}],
    "102": [{"name": "Friend", "email": "friend@gmail.com"}]
}

# =========================
# LOAD RESIDENT FACES (LBPH)
# =========================
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("Error: Could not load face cascade. Is OpenCV fully installed?")
    exit(1)

try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
except AttributeError:
    print("Error: Could not find LBPHFaceRecognizer.")
    print("Please run: pip install opencv-contrib-python")
    exit(1)

face_samples = []
face_ids = []
id_to_name = {}
current_id = 0

if not os.path.exists("residents"):
    os.makedirs("residents")

print("Traversing residents directory...")
for filename in os.listdir("residents"):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        filepath = os.path.join("residents", filename)
        
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Error loading image {filename}. Skipping...")
            continue
            
        faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        name = os.path.splitext(filename)[0]
        if len(faces) == 0:
            print(f"Warning: No face detected in {filename}. Please provide a clearer photo.")
            continue
            
        for (x, y, w, h) in faces:
            face_roi = img[y:y+h, x:x+w]
            face_samples.append(face_roi)
            
            if name not in id_to_name.values():
                id_to_name[current_id] = name
                current_id += 1
            
            assigned_id = [k for k, v in id_to_name.items() if v == name][0]
            face_ids.append(assigned_id)
            print(f"Loaded face for {name} with ID {assigned_id}")

if len(face_samples) > 0:
    print(f"Training recognizer on {len(face_samples)} face samples...")
    recognizer.train(face_samples, np.array(face_ids))
    print("Training complete!")
else:
    print("No faces could be processed. Everyone will be marked as 'Visitor'.")

# =========================
# DATABASE & LOGS
# =========================
def log_event(person_type, status, room, image_path, risk_score=0):
    try:
        conn = sqlite3.connect("visitor_logs.db")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO logs (timestamp, person_type, status, room, image_path, risk_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), person_type, status, room, image_path, risk_score))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

def send_request(endpoint):
    url = f"{ESP32_IP}:8080/{endpoint}"
    for _ in range(3):
        try:
            r = requests.get(url, timeout=2)
            print("ESP32:", r.text)
            return
        except:
            time.sleep(1)
    print("ESP32 not reachable")

# =========================
# RECONNECT
# =========================
cap = cv2.VideoCapture(STREAM_URL)

def reconnect():
    global cap
    cap.release()
    time.sleep(1)
    cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("ERROR: Cannot open stream")
    exit()

last_detection_time = 0
COOLDOWN = 5

# =========================
# MAIN CAMERA LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        reconnect()
        continue

    # Clean up the ESP32 feed slightly
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    frame = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces using the same Cascade
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    current_time = time.time()

    frame_has_resident = False
    best_resident_name = "Visitor"
    best_confidence = 100

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        
        name = "Visitor"
        is_resident = False
        
        # Test against recognizer
        if len(face_samples) > 0:
            label_id, confidence = recognizer.predict(face_roi)
            print(f"[DEBUG] LBPH Distance: {confidence:.1f} (Resident if < 65)")
            
            # Distance less than 65 is a STRICT match
            if confidence < 65:
                name = id_to_name.get(label_id, "Unknown")
                is_resident = True
                frame_has_resident = True
                best_resident_name = name
                best_confidence = confidence

        # =========================
        # DRAW BOUDING BOX
        # =========================
        color = (0, 255, 0) if is_resident else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # =========================
    # ACTION TRIGGER
    # =========================
    if len(faces) > 0 and (current_time - last_detection_time > COOLDOWN):
        image_path = f"visitor_{int(time.time())}.jpg"
        cv2.imwrite(image_path, frame)
        
        time_hour = datetime.now().hour

        if frame_has_resident:
            visit_count, _ = visitor_db.update_visitor(best_resident_name)
            risk = risk_score.calculate_risk(True, best_confidence, time_hour, visit_count)
            decision = risk_score.get_decision(risk)
            
            print(f"\n✅ {best_resident_name} → Decision: {decision} (Risk: {risk})")
            
            if decision == "OPEN":
                send_lcd("Access Granted")
                send_request("open")
                log_event(best_resident_name, "GRANTED", "-", image_path, risk)
            else:
                send_lcd("Access Denied")
                send_request("close")
                log_event(best_resident_name, "DENIED", "-", image_path, risk)
        else:
            print("\n🚨 Visitor → OTP Required")
            send_lcd("Enter Room No")
            
            # Release webcam so the user can use terminal without the video completely freezing
            cap.release()
            cv2.destroyAllWindows()
            
            print("\n" + "="*40)
            room = input(">>> PLEASE GO TO TERMINAL. Enter Room Number (e.g. 101): ")
            print("="*40)

            wrong_room = False
            wrong_otp = False
            
            if room not in ROOMS:
                print("❌ Invalid Room")
                send_lcd("Invalid Room")
                wrong_room = True
                cap = cv2.VideoCapture(STREAM_URL)
                last_detection_time = time.time()
                # Do not continue here, compute risk score and log the failure
            else:
                send_lcd(f"Room {room}")
                otp = random.randint(1000, 9999)

                print(f"Attempting to send OTP email to Room {room} occupants...")
                email_service.send_otp_to_roommates(
                    room_number=room,
                    roommates=ROOMS[room],
                    otp_code=otp,
                    image_path=image_path
                )

                print("Email service triggered\n")
                send_lcd("Check Email")
                time.sleep(2)
                
                send_lcd("Enter OTP")
                
                print("\n" + "="*40)
                user_input = input(">>> PLEASE GO TO TERMINAL. Enter OTP from email: ")
                print("="*40)

                if user_input != str(otp):
                    wrong_otp = True

            # Calculate Visitor Risk
            visit_count, wrong_attempts = visitor_db.update_visitor("Visitor", wrong_otp=wrong_otp)
            risk = risk_score.calculate_risk(False, 100, time_hour, visit_count, wrong_room, wrong_otp)
            decision = risk_score.get_decision(risk)
            
            if decision == "OPEN" and not wrong_otp and not wrong_room:
                print(f"✅ Access Granted (Risk: {risk})")
                send_lcd("Access Granted")
                send_request("open")
                log_event("Visitor", "GRANTED", room, image_path, risk)
            else:
                print(f"❌ Access Denied (Risk: {risk})")
                send_lcd("Access Denied")
                send_request("close")
                log_event("Visitor", "DENIED", room, image_path, risk)

            if not cap.isOpened():
                cap = cv2.VideoCapture(STREAM_URL)
            time.sleep(2)

        last_detection_time = time.time()

    cv2.imshow("Smart Visitor System - WEBCAM FEED", frame)

    if cv2.waitKey(1) & 0xFF == 27: # ESC key
        break

cap.release()
cv2.destroyAllWindows()