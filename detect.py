import cv2
import db
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("RTSP_USERNAME")
PASSWORD = os.getenv("RTSP_PASSWORD")
IP = os.getenv("RTSP_IP")

cap = cv2.VideoCapture(f"rtsp://{USERNAME}:{PASSWORD}@{IP}:554/stream1")

detector = cv2.FaceDetectorYN.create("./models/face_detection_yunet_2023mar.onnx", "", (1920,1080), 0.7)
recognizer = cv2.FaceRecognizerSF.create("./models/face_recognition_sface_2021dec.onnx", "")

db.init_db()

threshold = 0.50

database = db.load_faces()

# Shared between the reader thread and the main loop
latest_frame = None              # the newest frame from the camera, or None if it's already been taken
frame_lock = threading.Lock()    # only one thread may touch latest_frame at a time
stop_reading = threading.Event() # set by the main loop to tell the reader thread to stop

# Runs in a background thread: keeps reading the stream and keeps only the newest frame,
# so the main loop never works through a backlog of old frames
def read_frames():
    global latest_frame
    while not stop_reading.is_set():
        ok, frame = cap.read()
        if not ok:
            break  # stream ended or dropped
        with frame_lock:
            latest_frame = frame  # overwrite: any frame the main loop hasn't taken yet is dropped

# Returns the newest frame and marks it as taken, or None if no new frame has arrived yet
def take_latest_frame():
    global latest_frame
    with frame_lock:
        frame = latest_frame
        latest_frame = None
    return frame

def main():
    reader = threading.Thread(target=read_frames, daemon=True)
    reader.start()

    while True:
        frame = take_latest_frame()
        if frame is None:
            if not reader.is_alive():
                print("Camera stream ended")
                break
            time.sleep(0.005)  # no new frame yet; wait briefly instead of spinning the CPU
            continue

        # Tell the detector the real frame size, so it works with any camera
        frame_h, frame_w = frame.shape[:2]
        detector.setInputSize((frame_w, frame_h))

        embeddings = []  # one embedding per face in this frame, in the same order as the numbers on screen
        _, faces = detector.detect(frame)

        if faces is not None:
            for i, face in enumerate(faces):
                # x1, y1 are the coordinates of the top left corner of the box around the face
                # w, h = width, height respectively
                x1, y1, w, h = face[0:4].astype(int)
                x2 = x1 + w
                y2 = y1 + h

                aligned = recognizer.alignCrop(frame, face)
                cv2.imshow("aligned", aligned)

                embedding = recognizer.feature(aligned)
                embeddings.append(embedding)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                name = find_match(embedding)

                cv2.putText(frame, f"{i}: {name}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


        cv2.imshow("cam", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == ord("s"):
            chosen = choose_face(embeddings)
            if chosen is not None:
                name = input("Name: ")
                db.save_face(name, chosen)
                database.append((name, chosen))
                print("Saved!!")

    cap.release()
    cv2.destroyAllWindows()

# Returns the embedding of the face to save, or None if there's nothing valid to save
def choose_face(embeddings):
    if len(embeddings) == 0:
        print("No face in frame, nothing saved")
        return None

    if len(embeddings) == 1:
        return embeddings[0]

    try:
        index = int(input(f"Which face number? (0-{len(embeddings) - 1}): "))
    except ValueError:
        print("That's not a number, nothing saved")
        return None

    # Check the range ourselves: a negative index like -1 wouldn't raise an error
    if index < 0 or index >= len(embeddings):
        print(f"There is no face {index}, nothing saved")
        return None

    return embeddings[index]

def find_match(embedding):
    best_score = 0.0
    best_name = None
    for item in database:
        name, saved = item
        score = recognizer.match(embedding, saved, cv2.FaceRecognizerSF_FR_COSINE)

        if score > best_score:
            best_score = score
            best_name = name

    if best_score > threshold:
        return best_name
    else:
        return "unknown"

if __name__ == '__main__':
    main()
