import cv2
import requests
import random
import time
import sqlite3
import os
from datetime import datetime
from compreface import CompreFace
from email_service_ard import EmailService

WEB_CAM = False

ESP32_IP = "http://10.24.222.140"
STREAM_URL = f"{ESP32_IP}:81/stream"

email_service = EmailService()

API_KEY = "45319584-2196-4ab3-8c81-d960b173ef20"

compreface = CompreFace("http://localhost", "8000")
recognition = compreface.init_face_recognition(API_KEY)

print("Smart Visitor System running... Press ESC to exit")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# =========================
# RISK FUNCTION
# =========================
def calculate_risk(is_known, similarity, time_hour,
                   visit_count=1,
                   wrong_room=False,
                   wrong_otp=False):

    risk = 0

    if not is_known:
        risk += 10

    if time_hour < 6 or time_hour > 22:
        risk += 20

    if visit_count > 3:
        risk += 10

    if wrong_room:
        risk += 20

    if wrong_otp:
        risk += 30

    return risk

# CAMERA
if WEB_CAM:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(STREAM_URL)

def reconnect():
    global cap
    cap.release()
    time.sleep(1)
    if WEB_CAM:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(STREAM_URL)

def send_lcd(msg):
    try:
        requests.get(f"{ESP32_IP}:8080/lcd", params={"msg": msg}, timeout=2)
    except:
        pass

ROOMS = {
    "101": [{"name": "Rishitha", "email": "rishithav19@gmail.com"}],
    "102": [{"name": "Gnana", "email": "gnanaprasoona05@gmail.com"}]
}

def log_event(person_type, status, room, image_path):
    conn = sqlite3.connect("visitor_logs.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (timestamp, person_type, status, room, image_path)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          person_type, status, room, image_path))
    conn.commit()
    conn.close()

def send_request(endpoint):
    try:
        requests.get(f"{ESP32_IP}:8080/{endpoint}", timeout=2)
    except:
        pass

visit_counter = {}

last_detection_time = 0
COOLDOWN = 5
last_api_call = 0

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        reconnect()
        continue

    frame = cv2.resize(frame, (640, 480))
    current_time = time.time()

    label = "Detecting..."
    is_resident = False
    similarity = 0
    name = "Unknown"
    valid_detection = False

    # =========================
    # FACE DETECTION
    # =========================
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        label = "No Face Detected"

    else:
        if current_time - last_api_call > 2:
            last_api_call = current_time

            (x, y, w, h) = faces[0]

            # 🔥 Avoid tiny faces (ESP32 fix)
            if w < 80 or h < 80:
                continue

            face_img = frame[y:y+h, x:x+w]

            temp_path = "temp.jpg"
            cv2.imwrite(temp_path, face_img)

            try:
                result = recognition.recognize(
                    temp_path,
                    options={
                        "limit": 1,
                        "prediction_count": 1,
                        "det_prob_threshold": 0.8
                    }
                )

                print("\nFULL RESULT:", result)

                if len(result.get('result', [])) > 0:
                    subjects = result['result'][0].get('subjects', [])

                    if len(subjects) > 0:
                        data = subjects[0]
                        name = data['subject']
                        similarity = data['similarity']

                        print("Detected:", name)
                        print("Similarity:", similarity)

                        if similarity > 0.95:
                            label = f"{name} ({similarity:.2f})"
                            is_resident = True
                        else:
                            label = "Visitor"

                        valid_detection = True

                    else:
                        print("No subjects → Visitor")
                        label = "Visitor"
                        valid_detection = True

                else:
                    print("No face from CompreFace")
                    label = "No Face Detected"

            except Exception as e:
                print("Error:", e)
                label = "Error"

            try:
                os.remove(temp_path)
            except:
                pass

    # =========================
    # RISK ONLY IF VALID
    # =========================
    if valid_detection:
        visitor_id = name if is_resident else "visitor"
        visit_counter[visitor_id] = visit_counter.get(visitor_id, 0) + 1

        current_hour = datetime.now().hour

        risk_score = calculate_risk(
            is_known=is_resident,
            similarity=similarity,
            time_hour=current_hour,
            visit_count=visit_counter[visitor_id]
        )

        print("Risk Score:", risk_score)
    else:
        risk_score = 0

    # DISPLAY
    color = (0, 255, 0) if is_resident else (0, 0, 255)

    cv2.putText(frame, label, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    if valid_detection:
        cv2.putText(frame, f"Risk: {risk_score}", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    # SKIP if no valid detection
    if not valid_detection:
        cv2.imshow("Smart Visitor System", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    # =========================
    # ACTION CONTROL
    # =========================
    if current_time - last_detection_time > COOLDOWN:

        image_path = f"visitor_{int(time.time())}.jpg"
        cv2.imwrite(image_path, frame)

        if is_resident and risk_score < 50:
            print("\nAccess Granted:", label)
            send_lcd("Access Granted")
            send_request("open")
            log_event(label, "GRANTED", "-", image_path)
            time.sleep(2)

        else:
            print("\nVisitor Detected")

            if risk_score > 70:
                print("🚨 HIGH RISK VISITOR")
                send_lcd("HIGH RISK")

            send_lcd("Enter Room No")

            cap.release()
            cv2.destroyAllWindows()

            room = input("Enter Room Number: ")
            wrong_room = room not in ROOMS

            if wrong_room:
                print("Invalid Room")
                send_lcd("Invalid Room")
                reconnect()
                continue

            otp = random.randint(1000, 9999)

            email_service.send_otp_to_roommates(
                room_number=room,
                roommates=ROOMS[room],
                otp_code=otp,
                image_path=image_path
            )

            send_lcd("Enter OTP")
            user_input = input("Enter OTP: ")

            wrong_otp = user_input != str(otp)

            if not wrong_otp:
                print("Access Granted")
                send_lcd("Access Granted")
                send_request("open")
                log_event("Visitor", "GRANTED", room, image_path)
            else:
                print("Access Denied")
                send_lcd("Access Denied")
                send_request("close")
                log_event("Visitor", "DENIED", room, image_path)

            reconnect()
            time.sleep(2)

        last_detection_time = current_time

    cv2.imshow("Smart Visitor System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
