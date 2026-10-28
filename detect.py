import cv2

cap = cv2.VideoCapture(0)  # 0 = default camera

detector = cv2.FaceDetectorYN.create("./models/face_detection_yunet_2023mar.onnx", "", (1920,1080), 0.7)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    _, faces = detector.detect(frame)

    # CHANGED: "is not None" instead of "== None" (== on an array compares every element).
    if faces is not None:
        # CHANGED: faces is a table (one row per face), so loop over the rows.
        for face in faces:
            x1, y1, w, h = face[0:4].astype(int)
            x2 = x1 + w
            y2 = y1 + h
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # CHANGED: moved imshow (and the quit check) AFTER drawing, so the window shows the boxes.
    cv2.imshow("cam", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()
