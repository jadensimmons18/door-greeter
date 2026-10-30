import cv2

cap = cv2.VideoCapture(0)  # 0 = default camera

detector = cv2.FaceDetectorYN.create("./models/face_detection_yunet_2023mar.onnx", "", (1920,1080), 0.7)
recognizer = cv2.FaceRecognizerSF.create("./models/face_recognition_sface_2021dec.onnx", "")

saved = None

while True:
    ok, frame = cap.read() # Wait until the camera has a new frame ready
    if not ok:
        break

    embedding = None
    _, faces = detector.detect(frame)

    if faces is not None:
        for face in faces:
            # x1, y1 are the coordinates of the top left corner of the box around the face
            # w, h = width, height respectively
            x1, y1, w, h = face[0:4].astype(int)
            x2 = x1 + w
            y2 = y1 + h

            aligned = recognizer.alignCrop(frame, face)
            cv2.imshow("aligned", aligned)

            embedding = recognizer.feature(aligned)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # NEW: draw the 5 landmarks as red dots.
            # face[4:14] is 10 numbers: x, y, x, y, ... (one pair per landmark),
            # so reshape(5, 2) turns it into 5 rows of (x, y).
            landmarks = face[4:14].reshape(5, 2).astype(int)
            for (x, y) in landmarks:
                cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)


    cv2.imshow("cam", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == ord("s") and embedding is not None:
        saved = embedding
        print("Saved!!")


cap.release()
cv2.destroyAllWindows()
