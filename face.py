import cv2
import os
import numpy as np
import json

def train_model():
    print("Initializing face training...")
    
    # Path to the dataset
    data_path = "residents"
    
    if not os.path.exists(data_path):
        print(f"Error: Directory '{data_path}' does not exist.")
        return

    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        print("Error: Could not load face cascade. Is OpenCV installed cleanly?")
        return

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        print("Error: Could not find LBPHFaceRecognizer.")
        print("Please run: pip install opencv-contrib-python")
        return

    face_samples = []
    face_ids = []
    id_to_name = {}
    current_id = 0

    print("Traversing residents directory...")
    for filename in os.listdir(data_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            filepath = os.path.join(data_path, filename)
            
            img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Error loading image {filename}. Skipping...")
                continue
                
            faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            name = os.path.splitext(filename)[0]
            if len(faces) == 0:
                print(f"Warning: No face detected in {filename}.")
                continue
                
            for (x, y, w, h) in faces:
                face_roi = img[y:y+h, x:x+w]
                face_samples.append(face_roi)
                
                if name not in id_to_name.values():
                    id_to_name[current_id] = name
                    current_id += 1
                
                # Retrieve the assigned integer ID for this name string
                assigned_id = [k for k, v in id_to_name.items() if v == name][0]
                face_ids.append(assigned_id)
                print(f"Loaded face sample for '{name}' mapping to ID {assigned_id}")

    if len(face_samples) > 0:
        print(f"\nTraining recognizer on {len(face_samples)} face samples...")
        recognizer.train(face_samples, np.array(face_ids))
        
        # Save model and labels so scripts don't have to retrain dynamically!
        recognizer.write("trainer.yml")
        with open("labels.json", "w") as f:
            json.dump(id_to_name, f)
            
        print("✅ Training complete! Model securely saved to 'trainer.yml'.")
        print("✅ ID-to-Name labels saved to 'labels.json'.")
    else:
        print("❌ No valid faces could be processed for training.")

def test_model():
    print("\nStarting webcam to test the model... (Press 'q' or 'ESC' to exit)")
    
    if not os.path.exists("trainer.yml") or not os.path.exists("labels.json"):
        print("Error: Model files not found. Please train first.")
        return
        
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("trainer.yml")
    except Exception as e:
        print("Error loading model:", e)
        return

    with open("labels.json", "r") as f:
        # JSON keys are always strings, convert them back to integers
        id_to_name_str = json.load(f)
        id_to_name = {int(k): v for k, v in id_to_name_str.items()}
        
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open local webcam.")
        return
        
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            label_id, confidence = recognizer.predict(face_roi)
            
            # Use our strict threshold of 65
            if confidence < 65:
                name = id_to_name.get(label_id, "Unknown")
                color = (0, 255, 0) # Green for known
                text = f"{name} ({confidence:.1f})"
            else:
                name = "Visitor"
                color = (0, 0, 255) # Red for unknown
                text = f"{name} ({confidence:.1f})"
                
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Face Model Tester", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    train_model()
    test_model()
