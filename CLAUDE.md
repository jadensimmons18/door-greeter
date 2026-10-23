# Door Greeter

## Project summary

A solo side project to build a device with a camera that notices when someone walks in through a door and greets them by name. To do this it must:

1. Detect that a person **entered** the room (as opposed to leaving it).
2. Work out **who** the person is.
3. **Remember** their name, so the greeting is personalized.

The owner is a computer science student with **no prior computer vision experience**, so this is also a learning project.

## Current status

- Coding has **not started**.
- The first milestone is a **prototype running on a laptop, using an iPhone as the camera** (not the laptop's built-in webcam). Dedicated hardware comes later.

## Scope and phases

**Phase 1 (current target): laptop prototype with an iPhone camera**
- Read frames from the iPhone camera.
- Detect faces in each frame.
- Recognize known people and print or display their names.

**Later phases (not yet planned in detail):**
- Detecting entry vs. leaving
- Storing and managing known people (enrollment)
- Spoken or on-screen greeting logic
- Moving from the laptop to dedicated hardware at a real door

The order and details of the later phases are open and will be decided as the project progresses.

## Decisions

| Topic | Status |
|---|---|
| First target | Prototype on a laptop (decided) |
| Camera | **iPhone** instead of the laptop webcam (decided) |
| How the iPhone feeds video to the laptop | **Undecided** (e.g. Continuity Camera, a camera-streaming app, or another method). Not yet chosen. |
| Face detection/recognition stack | **Undecided.** OpenCV (YuNet detector + SFace recognizer) is being used to get started; InsightFace is a possible alternative. Revisit once the pipeline works. |
| Entry vs. leaving logic | **Undecided.** Options discussed: an inward-facing camera so only approaching faces are detected, or tracking people across frames and detecting the direction they cross a line. |
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
- Files created so far (in the walkthrough, not yet confirmed to exist in the repo): `cam_test.py` (camera check) and `detect.py` (face detection with YuNet)
- Note: those scripts were written for a laptop webcam (`cv2.VideoCapture(0)`). Since the camera is an iPhone, the video source line will need to change depending on how the iPhone is connected.

## How Claude should work on this project

The owner wants to learn, not just receive code.

- **Explain the concept first, then show the code.** Frame each step conceptually (what problem it solves, why this approach) before implementing.
- **Go step by step**, one small milestone at a time, rather than handing over a full solution.
- **Explain what the code is doing**, including what the key lines, parameters and return values mean.
- Where a parameter affects behavior (e.g. detection confidence threshold), point it out and suggest a small experiment so the owner builds intuition.
- If the owner asks for a specific code snippet (e.g. "write a test for X"), give just the short code without a long walkthrough.
- **Do not assume the owner's intentions.** If a design choice is open, or a request is ambiguous, ask instead of deciding.

## Open questions to resolve with the owner

- How to connect the iPhone camera to the laptop
- Which CV stack to commit to
- How to handle entry vs. leaving
- Target hardware
- How greetings are delivered
- Where and how data is stored, and the privacy/consent approach for storing people's biometric data