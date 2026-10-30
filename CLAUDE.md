# Door Greeter

## Project summary

A solo side project to build a device with a camera that notices when someone walks in through a door and greets them by name. To do this it must:

1. Detect that a person **entered** the room (as opposed to leaving it).
2. Work out **who** the person is.
3. **Remember** their name, so the greeting is personalized.

The owner is a computer science student with **no prior computer vision experience**, so this is also a learning project.

## Current status

- Live face **detection** works (`detect.py`). Face **recognition** is next.
- The first milestone is a **prototype running on a Mac mini, using an iPhone as the camera** (the Mac mini has no camera of its own). Dedicated hardware comes later.

## Scope and phases

**Phase 1 (current target): Mac mini prototype with an iPhone camera**
- Read frames from the iPhone camera.
- Detect faces in each frame.
- Recognize known people and print or display their names.

**Later phases (not yet planned in detail):**
- Detecting entry vs. leaving
- Storing and managing known people (enrollment)
- Spoken or on-screen greeting logic
- Moving from the Mac mini to dedicated hardware at a real door

The order and details of the later phases are open and will be decided as the project progresses.

## Decisions

| Topic | Status |
|---|---|
| First target | Prototype on a Mac mini (desktop, no built-in camera) (decided) |
| Camera | **iPhone** (decided) |
| How the iPhone feeds video to the Mac | **Continuity Camera** (decided). Chosen for low setup and good image quality; a Wi-Fi streaming app was the alternative, if the phone ever needs to sit away from the Mac. |
| Face detection/recognition stack | **Undecided.** OpenCV (YuNet detector + SFace recognizer) is being used to get started; InsightFace is a possible alternative. Revisit once the pipeline works. |
| Entry vs. leaving logic | **Undecided.** Options discussed: an inward-facing camera so only approaching faces are detected, or tracking people across frames and detecting the direction they cross a line. |
| Where recognition happens | **A face-level camera at the entry (doorbell-style)** (decided). Ceiling-corner cameras see faces from too high and too small to recognize reliably. |
| Room cameras | **Later phase** (decided). The long-term vision is a home security/automation system with cameras in the top corners of rooms; those would detect and track people (possibly using person re-identification), not recognize faces. |
| 2D vs. depth/infrared sensing | **2D (normal camera) for the prototype** (decided). Depth (e.g. Intel RealSense, OAK-D) could add anti-spoofing, and infrared could add low-light recognition; revisit both when choosing final hardware, especially if the system will unlock doors or handle security. |
| Final hardware | **Undecided** |
| Greeting output (speech engine, on-screen, etc.) | **Undecided** |
| Where data is stored (names, embeddings) | **Undecided** |
| Privacy and consent approach | **Undecided** |

Do not treat any "Undecided" item as settled. Ask the owner before choosing for them.

## Conceptual pipeline

Each video frame is meant to flow through:

frame → detect faces → turn each face into an embedding → compare to known people → name

- **Detection** answers "where are the faces?" (bounding boxes, plus facial landmarks).
- **Recognition** answers "whose face is it?" by comparing embeddings (numeric vectors) against stored ones for known people.
- These two questions are kept as separate steps in the code.

## Environment

- Language: Python
- Uses a per-project virtual environment (`python -m venv .venv`), activated before installing packages.
- Packages so far: `opencv-python`, `numpy`
- Files so far: `cam_test.py` (live camera view) and `detect.py` (live face detection with YuNet; needs `models/face_detection_yunet_2023mar.onnx`, downloaded from the `opencv/opencv_zoo` repo). The score threshold had to be lowered from the default 0.9, because faces scored only about 0.90.
- With Continuity Camera, the iPhone shows up as an ordinary camera number in `cv2.VideoCapture(n)`. The Mac mini has no other camera, so it is normally `0`, but the number isn't guaranteed.
- If the iPhone doesn't appear as a camera: first check FaceTime/Photo Booth's Video menu (if it's missing there, macOS hasn't connected to it, so OpenCV can't either). A **USB cable** most likely fixed it the first time; Wi-Fi and Bluetooth on both devices, same Apple ID and Handoff on are the other requirements.

## How Claude should work on this project

The owner wants to learn, not just receive code.

- **Explain the concept first, then show the code.** Frame each step conceptually (what problem it solves, why this approach) before implementing.
- **Go step by step**, one small milestone at a time, rather than handing over a full solution.
- **Explain what the code is doing**, including what the key lines, parameters and return values mean.
- Where a parameter affects behavior (e.g. detection confidence threshold), point it out and suggest a small experiment so the owner builds intuition.
- If the owner asks for a specific code snippet (e.g. "write a test for X"), give just the short code without a long walkthrough.
- **Do not assume the owner's intentions.** If a design choice is open, or a request is ambiguous, ask instead of deciding.

## Open questions to resolve with the owner

- Which CV stack to commit to
- How to handle entry vs. leaving
- Target hardware
- How greetings are delivered
- Where and how data is stored, and the privacy/consent approach for storing people's biometric data