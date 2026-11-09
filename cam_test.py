import cv2
import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("RTSP_USERNAME")
PASSWORD = os.getenv("RTSP_PASSWORD")
IP = os.getenv("RTSP_IP")

cap = cv2.VideoCapture(f"rtsp://{USERNAME}:{PASSWORD}@{IP}:554/stream1")

while True:
    ok, frame = cap.read()
    if not ok:
        break
    cv2.imshow("cam", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()