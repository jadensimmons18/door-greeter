# Door Greeter

## Project summary

A solo side project that starts as a device that notices when someone walks in through a door and greets them by name. The long-term goal is an **easy, intuitive home automation system**: it knows when people enter and leave the house and its rooms, recognizes who they are, and runs automations (lights, appliances and other tasks). To do this it must:

1. Detect that a person **entered** (as opposed to leaving).
2. Work out **who** the person is.
3. **Remember** known people, so greetings and automations are personalized.

The owner is a senior computer science student who is comfortable with Python and programming, but this is their **first computer vision project**, so it's also a learning project.

## Current status

- Live face **detection and recognition** work (`detect.py`), running on a Mac mini with an iPhone as the camera.
- Known faces are saved to and loaded from **SQLite** (`db.py`). Pressing `s` saves a face; when several faces are in frame, each is numbered on screen and the owner types which one to save.
- **Next:** the doorbell camera prototype (step 1 of the plan below).

## Plan

Get one complete path working (person arrives → recognized → entry confirmed → something happens) before expanding.

1. **Doorbell prototype (current).** iPhone pointed out a window or door. Detect and track people, recognize them, and notice when a track ends at the door (someone went in) or starts at the door (someone came out): e.g. print "jaden disappeared at the door". See "Doorbell camera requirements" below.
2. **Inside camera prototype.** iPhone mounted inside by the door, facing **into** the house with a wide-angle lens; recognize people walking toward the door (leaving) and see the backs of people walking in (entering).
3. **Combine them.** A person disappears at the door on one camera, and a person appears from the door on the other within a short time window. Outside → inside = "X arrived home"; inside → outside = "X left". With only one iPhone, record test videos from each position and process them together.
4. **Trigger actions** by sending events (e.g. `jaden entered`) to Home Assistant.
5. **Later:** room-level cameras, carrying identity between rooms, real hardware.

## Decisions

| Topic | Status |
|---|---|
| First target | Prototype on a Mac mini (desktop, no built-in camera) (decided) |
| Camera | **iPhone** for prototyping (decided) |
| How the iPhone feeds video to the Mac | **Continuity Camera** (decided). Chosen for low setup and good image quality; a Wi-Fi streaming app was the alternative, if the phone ever needs to sit away from the Mac. |
| Face detection/recognition stack | **Undecided.** OpenCV (YuNet detector + SFace recognizer) is in use; InsightFace is a possible alternative. Revisit once the pipeline works. |
| Camera layout at the front door | **Two cameras** (decided). An outdoor, face-level **doorbell camera** (Ring-style), and an **inside camera by the door facing into the house** with a wide-angle lens. Each camera sees faces in one direction and backs in the other: the doorbell sees the faces of people arriving, and the inside camera sees the faces of people leaving. Rejected alternatives: an indoor camera facing the door (would stand out too much in most homes) and an above-door camera looking down (can't see faces, so it couldn't tell who left). |
| Entry vs. leaving logic | **Camera-only, decided in outline.** A crossing is when a person **disappears at the door** on one camera (their track ends right at the door) and a person **appears from the door** on the other (their track starts at the edge of the frame nearest the door) within a short time window. Outside → inside = arrived; inside → outside = left. The same logic serves both directions. Because the inside camera sees backs on arrival, people are matched across cameras by **timing and counts**, not by face: "one person disappeared outside, one appeared inside". Requiring the disappear/appear to happen at the door (a "virtual door sensor") rules out coincidences, like a roommate walking past inside while a delivery driver is outside. Details (time window, door zones in each image, several people at once, quick trips out) are still to be worked out. |
| Box size (approaching = box grows) | **Rejected as the main signal**, but can be a supporting clue. It assumes people walk straight at the camera. In apartment hallways people approach from the side, neighbors walk past constantly, and someone unlocking the door barely moves. |
| Door sensor | **Optional, later** (decided). Build camera-only first; add a sensor only if testing shows false alarms. Then the rule is: only count a crossing if the door actually opened. Options: a DIY reed switch on the camera Pi's GPIO (~$3), an off-the-shelf Zigbee/Wi-Fi contact sensor in Home Assistant, or a smart lock that reports how it was unlocked. During development, door events can be simulated with a key press. |
| Apartments | The owner lives in an apartment, so expect hallway approaches and passing neighbors. A camera in a shared hallway may not be allowed by the lease or local rules; a **peephole camera** is a renter-friendly, face-level alternative. |
| Who left | **Decided:** recognized by face on the inside camera as they walk toward the door. |
| Wide-angle lens | Faces near the image edges get distorted, which can hurt recognition. OpenCV undistortion can fix this if needed. |
| Notifications | **Both** (decided): one when someone **arrives** at the door, and another once their **entry is confirmed** by the inside camera. The same applies to leaving. Each includes a short clip. How they reach the phone is **undecided**; the Home Assistant companion app (supports notifications with images/video) was suggested instead of building a custom app. |
| Unknown people | **Notify without saving** (decided): send "unknown person" notifications with a clip, but never store their face or embedding. |
| Room cameras | **Later phase** (decided). Above-door cameras in each room to count people in and out. They can't see faces, so identity needs another source: person re-identification across cameras (hard) or phone presence (Bluetooth/Wi-Fi). Which one is **undecided**. |
| Automations | **Home Assistant** (decided): the system sends events to it (probably over MQTT) instead of controlling lights and devices itself. |
| 2D vs. depth/infrared sensing | **2D (normal camera) for the prototype** (decided). Depth (e.g. Intel RealSense, OAK-D) could add anti-spoofing, and infrared is needed for the doorbell camera at night; revisit both when choosing final hardware, especially if the system will unlock doors or handle security. |
| Final hardware | **Central hub design** (decided). Each camera is a low-end Raspberry Pi that only **streams** video (e.g. over RTSP) to one central hub, which runs all the CV. The hub is the Mac mini for now. Chosen for cost, power use, one place to update the code, and keeping the face database inside the home (not on the outdoor device). Ring/Nest work similarly, with the cloud as their hub. Suggested camera board: Raspberry Pi Zero 2 W + Camera Module 3 (not yet bought). Still undecided: the hub's long-term hardware, how cameras are powered (PoE, doorbell wiring), and the outdoor enclosure. Battery power isn't viable for always-on vision. |
| Greeting output (speech engine, on-screen, etc.) | **Undecided** |
| Where data is stored (names, embeddings) | **SQLite** (decided), loaded into memory for comparisons. The database file stays on the local machine and out of git. |
| Privacy and consent approach | **Partly decided.** Only enrolled people's embeddings are stored; unknown faces never are. Still open: privacy zones (masking the sidewalk or neighbors), clip retention/auto-delete, and how the inside camera avoids continuous recording inside the home (suggested: only save clips around door events). Check local laws on recording public areas and storing biometric data. |

Do not treat any "Undecided" item as settled. Ask the owner before choosing for them.

## Doorbell camera requirements

Unlike a typical doorbell (motion → record a few seconds → send the clip), this one identifies people and knows whether they're arriving or leaving.

**Prototype (must have):**
1. **Recognize people** approaching, using the existing face recognition against the database and threshold.
2. **One event per visit, not per frame.** Track each person across frames, so someone standing at the door produces one notification, not hundreds.
3. **Decide identity over several frames** (e.g. "jaden" in most of the recent frames), not from a single frame.
4. **Notice crossings at the door.** Mark a door zone in the image. A track that ends in the door zone means someone went in; a track that starts there means someone came out. Box size is only a supporting clue (see Decisions).
5. **Being at the door isn't entering.** Passers-by in the hallway, delivery drivers and visitors who leave again must not be reported as entering; "arrived" needs a matching appearance from the door on the inside camera.
6. **Notifications:** "X arrived" (or "unknown person at the door"), then "X entered" once confirmed; likewise for leaving. Each with a short clip.
7. **Pre-roll clips:** keep the last few seconds of frames in memory, so a clip starts before the moment of detection.
8. **Unknown people:** notify, but never store their face.
9. **Event log** in SQLite: who, when, direction, clip path.

**Later:**
- A "who's home" state, updated by entries and exits (for Home Assistant automations)
- Several people at once: one notification each or combined (undecided)
- Night (infrared) and backlight
- Spoofing: a photo of a resident fools it. Fine for notifications, but it must **never unlock doors** without a liveness check.
- Privacy zones and clip auto-deletion
- Enrollment from the app, and updating people's saved faces over time
- Graceful failures: queue events if the network drops, and alert if a camera goes offline

## Conceptual pipeline

Each video frame is meant to flow through:

frame → detect faces → turn each face into an embedding → compare to known people → name

- **Detection** answers "where are the faces?" (bounding boxes, plus facial landmarks).
- **Recognition** answers "whose face is it?" by comparing embeddings (numeric vectors) against stored ones for known people.
- These two questions are kept as separate steps in the code.
- Entry/exit detection will add **person** detection and **tracking** across frames. Whole bodies, not just faces, because people walking away show their backs.

## Environment

- Language: Python
- Uses a per-project virtual environment (`python -m venv .venv`), activated before installing packages.
- Packages so far: `opencv-python`, `numpy`
- Files so far:
  - `cam_test.py`: live camera view.
  - `detect.py`: live face detection (YuNet) and recognition (SFace). Needs `models/face_detection_yunet_2023mar.onnx` and `models/face_recognition_sface_2021dec.onnx`, both from the `opencv/opencv_zoo` repo. Uses cosine similarity with a threshold of 0.50; OpenCV suggests about 0.363 for SFace. The detector's score threshold had to be lowered from the default 0.9, because faces scored only about 0.90.
  - `db.py`: SQLite storage. A `faces` table with `id`, `name` and `embedding BLOB`. Embeddings are stored with `.tobytes()` and loaded with `np.frombuffer(..., dtype=np.float32).reshape(1, 128)`.
- With Continuity Camera, the iPhone shows up as an ordinary camera number in `cv2.VideoCapture(n)`. The Mac mini has no other camera, so it is normally `0`, but the number isn't guaranteed.
- If the iPhone doesn't appear as a camera: first check FaceTime/Photo Booth's Video menu (if it's missing there, macOS hasn't connected to it, so OpenCV can't either). A **USB cable** most likely fixed it the first time; Wi-Fi and Bluetooth on both devices, same Apple ID and Handoff on are the other requirements.
- OpenCV 5 prints `setPreferableTarget ... not supported by the new graph engine` warnings when loading the models. They're harmless.

## How Claude should work on this project

The owner wants to learn, not just receive code.

- **Explain the concept first, then show the code.** Frame each step conceptually (what problem it solves, why this approach) before implementing.
- **Go step by step**, one small milestone at a time, rather than handing over a full solution.
- **Explain what the code is doing**, including what the key lines, parameters and return values mean.
- Pitch explanations at a senior CS student: explain the CV concepts and the APIs that are new to them, not programming basics.
- Read the current code before answering, so you don't re-teach what's already built.
- Where a parameter affects behavior (e.g. detection confidence threshold), point it out and suggest a small experiment so the owner builds intuition.
- If the owner asks for a specific code snippet (e.g. "write a test for X"), give just the short code without a long walkthrough.
- **Do not assume the owner's intentions.** If a design choice is open, or a request is ambiguous, ask instead of deciding.

## Open questions to resolve with the owner

- Which CV stack to commit to (including which person detector and tracker: YOLO via `ultralytics`, a model through OpenCV's DNN module, or OpenCV's HOG detector)
- How notifications reach the phone (Home Assistant companion app or a custom app)
- Several people at once: one notification each or combined
- Identity for room cameras: re-identification or phone presence
- Target hardware (including infrared for the doorbell at night)
- How greetings are delivered
- The privacy/consent approach for storing people's biometric data
