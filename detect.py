import cv2

cap = cv2.VideoCapture(0)  # 0 = default camera

detector = cv2.FaceDetectorYN.create("./models/face_detection_yunet_2023mar.onnx", "", (1920,1080), 0.7)
recognizer = cv2.FaceRecognizerSF.create("./models/face_recognition_sface_2021dec.onnx", "")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    _, faces = detector.detect(frame)

    if faces is not None:
        for face in faces:
            # x1, y1 are the coordinates of the top left corner of the box around the face
            # w, h = width, height respectively
            x1, y1, w, h = face[0:4].astype(int)
            x2 = x1 + w
            y2 = y1 + h
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            aligned = recognizer.alignCrop(frame, face)
            cv2.imshow("aligned", aligned)


    cv2.imshow("cam", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()
