# Door Greeter

## Project summary

A solo side project that starts as a device that notices when someone walks in through a door and greets them by name. The long-term goal is an **easy, intuitive home automation system**: it knows when people enter and leave the house, recognizes who they are, and runs automations (lights, appliances and other tasks). To do this it must:

1. Detect that a person **entered** (as opposed to leaving).
2. Work out **who** the person is.
3. **Remember** known people, so greetings and automations are personalized.

The owner is a senior computer science student who is comfortable with Python and programming, but this is their **first computer vision project**, so it's also a learning project.

## Current status

- Live face **detection and recognition** work (`detect.py`), running on a Mac mini with an iPhone as the camera.
- Known faces are saved to and loaded from **SQLite** (`db.py`). Pressing `s` saves a face; when several faces are in frame, each is numbered on screen and the owner types which one to save.
- **Next:** the outdoor camera prototype (step 1 of the plan below).

## Plan

Get one complete path working (person arrives → recognized → entry confirmed → something happens) before expanding.

The owner confirmed this order. See "Presence detection" for the design.

1. **Outdoor camera prototype (current).** iPhone pointed out a window or door. Detect and track people, recognize arriving residents by face, and save an appearance embedding (clothing, height, build) for each of them for the day. The camera handles identity only. Until the mmWave sensor exists, simulate door events (inbound/outbound) with a key press. See "Doorbell camera requirements" below.
2. **Re-ID on departure.** Match a departing person, often seen from behind, against the day's appearance embeddings of the people currently inside.
3. **Home-state model.** A "who's home" state for each resident, with a confidence score. Assign each door event to the candidates the state allows, and mark low-confidence events as "unidentified".
4. **Phone presence.** Add Wi-Fi and BLE phone detection (GPS geofencing optional) as a second identity source, and combine it with the camera's match scores.
5. **mmWave sensor.** Replace the simulated door events with real inbound/outbound events from the radar, including several people at once.
6. **Trigger actions** by sending events (e.g. `jaden entered`) to Home Assistant.
7. **Later:** real hardware, more exterior doors.

## Decisions

| Topic | Status |
|---|---|
| First target | Prototype on a Mac mini (desktop, no built-in camera) (decided) |
| Camera | **iPhone** for prototyping (decided) |
| How the iPhone feeds video to the Mac | **Continuity Camera** (decided). Chosen for low setup and good image quality; a Wi-Fi streaming app was the alternative, if the phone ever needs to sit away from the Mac. |
| Face detection/recognition stack | **Undecided.** OpenCV (YuNet detector + SFace recognizer) is in use; InsightFace is a possible alternative. Revisit once the pipeline works. |
| Camera layout at the front door | **One outdoor camera per exterior door, and no interior cameras** (decided). It's used for identity, not direction. This replaces the earlier two-camera plan, which had an inside camera facing into the house. See "Presence detection" below. |
| Entry vs. leaving logic | **An mmWave radar sensor at each exterior door** (decided). This replaces the earlier camera-only plan and any single IR break-beam. See "Presence detection" below. |
| Box size (approaching = box grows) | **Not used for direction**; the mmWave sensor handles direction. It was rejected even as a camera signal: it assumes people walk straight at the camera, but in apartment hallways people approach from the side, neighbors walk past constantly, and someone unlocking the door barely moves. |
| Door sensor | **Optional, later** (decided). The mmWave sensor is the main direction sensor. A door contact sensor could be added if testing shows false alarms, with the rule: only count a crossing if the door actually opened. Options: a DIY reed switch on a Pi's GPIO (~$3), an off-the-shelf Zigbee/Wi-Fi contact sensor in Home Assistant, or a smart lock that reports how it was unlocked. During development, door events can be simulated with a key press. |
| Apartments | The owner lives in an apartment, so expect hallway approaches and passing neighbors. A camera in a shared hallway may not be allowed by the lease or local rules; a **peephole camera** is a renter-friendly, face-level alternative. |
| Who left | **Decided:** person re-identification on the outdoor camera, combined with phone presence. See "Presence detection" below. |
| Wide-angle lens | Only relevant if the outdoor camera uses one. Faces near the image edges get distorted, which can hurt recognition. OpenCV undistortion can fix this if needed. |
| Notifications | **Both** (decided): one when someone **arrives** at the door, and another once their **entry is confirmed** by the mmWave sensor. The same applies to leaving. Each includes a short clip. How they reach the phone is **undecided**; the Home Assistant companion app (supports notifications with images/video) was suggested instead of building a custom app. |
| Unknown people | **Notify without saving** (decided): send "unknown person" notifications with a clip, but never store their face or embedding. |
| Room cameras | **Dropped** (decided). No interior cameras, for privacy and cost. See "Presence detection". |
| Automations | **Home Assistant** (decided): the system sends events to it (probably over MQTT) instead of controlling lights and devices itself. |
| 2D vs. depth/infrared sensing | **2D (normal camera) for the prototype** (decided). Depth (e.g. Intel RealSense, OAK-D) could add anti-spoofing, and infrared is needed for the doorbell camera at night; revisit both when choosing final hardware, especially if the system will unlock doors or handle security. |
| Final hardware | **Central hub design** (decided). Each camera is a low-end Raspberry Pi that only **streams** video (e.g. over RTSP) to one central hub, which runs all the CV. The hub is the Mac mini for now. Chosen for cost, power use, one place to update the code, and keeping the face database inside the home (not on the outdoor device). Ring/Nest work similarly, with the cloud as their hub. Suggested camera board: Raspberry Pi Zero 2 W + Camera Module 3 (not yet bought). Each exterior door also gets an mmWave radar sensor. Still undecided: which mmWave sensor and how it reports to the hub, the hub's long-term hardware, how cameras are powered (PoE, doorbell wiring), and the outdoor enclosure. Battery power isn't viable for always-on vision. |
| Greeting output (speech engine, on-screen, etc.) | **Undecided** |
| Where data is stored (names, embeddings) | **SQLite** (decided), loaded into memory for comparisons. The database file stays on the local machine and out of git. |
| Privacy and consent approach | **Partly decided.** Only enrolled people's embeddings are stored; unknown faces never are. There are no interior cameras. Still open: privacy zones (masking the sidewalk or neighbors), clip retention/auto-delete, and deleting the daily appearance embeddings once the day is over. Check local laws on recording public areas and storing biometric data. |

Do not treat any "Undecided" item as settled. Ask the owner before choosing for them.

## Presence detection

How the system knows who entered or left the house. Three parts: a sensor for **direction**, phone presence and an outdoor camera for **identity**, and a **home-state model** that combines them.

**1. Direction (entered vs. exited): mmWave radar**
- One mmWave radar sensor mounted at each exterior door.
- Determines the direction of motion through the doorway (inbound or outbound).
- Must handle several people passing through together (a count and a direction for each person), which a simple break-beam can't.
- Replaces any earlier plan that used inside-facing cameras or single IR break-beams for direction.

**2. Identity: phone presence and the outdoor camera, combined**
- **Phone presence:** detect each resident's phone through home Wi-Fi connect/disconnect, Bluetooth (BLE) proximity scanning, and optionally GPS geofencing from a companion app.
- **Outdoor camera** (one per exterior door, outside only; no interior cameras):
  - **On arrival:** face recognition against enrolled residents. Also save an appearance embedding (clothing, height, build) for that person for the day.
  - **On departure:** person re-identification (re-ID). Match the departing person's appearance, often seen from behind, against the stored appearance embeddings of the people currently inside.
- Neither source alone is trusted as final. Identity comes from combining both.

**3. Home-state model and sensor fusion**
- Keep a "who's home" state for each resident, with a confidence score.
- On a door event from the mmWave sensor, the only candidates are the people the state says are outside (for an entry) or inside (for an exit). If there's only one candidate, assign the event to them directly.
- Combine the mmWave direction, phone presence changes within a time window around the event, and camera face/re-ID match scores into one decision.
- When sources disagree, weight the evidence instead of trusting one source, and log the disagreement. For example, a phone still at home while the camera's re-ID strongly matches a departing resident suggests a forgotten phone.
- If confidence is below a threshold, mark the event as an "unidentified entry/exit" and resolve it later when another signal arrives (phone reconnects, camera sighting, etc.).

**4. Edge cases to handle**
- Groups entering or leaving together.
- Tailgating, or a door held open.
- Phone left at home, or phone dead or switched off.
- Visitors and unknown people (no enrolled phone or face) are tracked as guests, not residents.
- Poor camera conditions: night, rain, face not visible.

**5. Why this design**
- No interior cameras, for privacy and lower cost, since the product may be sold later.
- Phone presence is cheap and needs no extra hardware. The camera covers forgotten phones and people without phones. mmWave gives reliable direction without capturing images.

## Doorbell camera requirements

Unlike a typical doorbell (motion → record a few seconds → send the clip), this one identifies people. Whether they're arriving or leaving comes from the mmWave sensor (see "Presence detection").

**Prototype (must have):**
1. **Recognize people** approaching, using the existing face recognition against the database and threshold.
2. **One event per visit, not per frame.** Track each person across frames, so someone standing at the door produces one notification, not hundreds.
3. **Decide identity over several frames** (e.g. "jaden" in most of the recent frames), not from a single frame.
4. **Save an appearance embedding on arrival** (clothing, height, build) for the day, so the person can be re-identified when they leave.
5. **Being at the door isn't entering.** Passers-by in the hallway, delivery drivers and visitors who leave again must not be reported as entering; an entry needs an inbound event from the mmWave sensor (simulated with a key press until the sensor exists).
6. **Notifications:** "X arrived" (or "unknown person at the door"), then "X entered" once the mmWave sensor confirms it; likewise for leaving. Each with a short clip.
7. **Pre-roll clips:** keep the last few seconds of frames in memory, so a clip starts before the moment of detection.
8. **Unknown people:** notify, but never store their face.
9. **Event log** in SQLite: who, when, direction, clip path.

**Later:**
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
- Re-identifying people as they leave will add **person** detection and **tracking** across frames. Whole bodies, not just faces, because people walking away show their backs. Direction comes from the mmWave sensor, not the camera.

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
- Which mmWave radar sensor, and how it reports events to the hub
- How phone presence is detected in practice (Wi-Fi, BLE scanning, a companion app with GPS) and whether it goes through Home Assistant
- Which re-ID model to use for appearance embeddings
- The fusion details: time windows, how each source is weighted, and the confidence threshold for "unidentified" events
- Target hardware (including infrared for the doorbell at night)
- How greetings are delivered
- The privacy/consent approach for storing people's biometric data
