# Door Greeter

## Project summary

A solo side project that starts as a device that notices when someone walks in through a door and greets them by name. The long-term goal is an **easy, intuitive home automation system**: it knows when people enter and leave the house, recognizes who they are, and runs automations (lights, appliances and other tasks). To do this it must:

1. Detect that a person **entered** (as opposed to leaving).
2. Work out **who** the person is.
3. **Remember** known people, so greetings and automations are personalized.

The owner is a senior computer science student who is comfortable with Python and programming, but this is their **first computer vision project**, so it's also a learning project.

## Current status

- Live face **detection and recognition** work (`detect.py`), running on a Mac mini. The camera is a **Tapo camera over RTSP** (credentials in `.env`); the iPhone via Continuity Camera was used before that.
- Known faces are saved to and loaded from **SQLite** (`db.py`). Pressing `s` saves a face; when several faces are in frame, each is numbered on screen and the owner types which one to save.
- RTSP lag is fixed with a background reader thread that keeps only the newest frame, and faces are detected on a downscaled copy of each frame (`DETECT_WIDTH`).
- **Per-face tracking was tried and dropped** (see "Visit logic" below for why). `tracker.py` is kept but not used.
- **Next:** the doorbell visit logic (see "Doorbell visit logic").
- **Next:** the outdoor camera prototype (step 1 of the plan below).

## Plan

Get one complete path working (person arrives → recognized → entry confirmed → something happens) before expanding.

1. **Doorbell prototype (current).** Camera pointed at the door from outside. Group detections into **visits**, recognize who's there over the visit, and print "X unknown people are at your door" when appropriate. See "Doorbell visit logic" below.
2. **mmWave sensor prototype.** An **HLK-LD2450** mounted on the inside, on top of the door frame, reports people's positions, so the system can tell someone walking **in** from someone walking **out**.
3. **Combine them.** A doorbell visit followed by an inward crossing on the mmWave sensor = "X arrived home". An outward crossing = "X left" (who left: see Decisions).
4. **Trigger actions** by sending events (e.g. `jaden entered`) to Home Assistant.
5. **Later:** room-level sensing, carrying identity between rooms, real hardware.
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
| Camera | A **Tapo camera over RTSP** is in use for prototyping. The iPhone via **Continuity Camera** was used before (chosen for low setup and good image quality). |
| Face detection/recognition stack | **Undecided.** OpenCV (YuNet detector + SFace recognizer) is in use; InsightFace is a possible alternative. Revisit once the pipeline works. |
| Front door layout | **Doorbell camera + mmWave sensor** (decided). An outdoor, face-level **doorbell camera** (Ring-style) sees and recognizes people arriving. An **HLK-LD2450 mmWave radar** (owner has one) on a mount on the **inside top of the door frame** tells which direction people cross the door. It replaced the earlier plan of an inside camera facing into the house, because it gives **more privacy** (no video inside the home) and makes **direction easier to tell**. The LD2450 reports x/y positions of up to 3 targets, which is what direction needs (a presence-only sensor like the LD2410 wouldn't be enough). Rejected earlier: an indoor camera facing the door (stands out in most homes) and an above-door camera looking down (can't see faces). |
| Per-face tracking | **Dropped for now** (decided). An IoU + face-embedding tracker was built (`tracker.py`) but fragmented badly: while someone walks around, most frames show a turned or blurred face, and SFace similarity for the *same* person ranged from 0.06 to 0.90, so one person became many tracks. Replaced by **visit-level logic** (see "Doorbell visit logic"). Body tracking (e.g. a person detector) may come back later if the door-crossing logic needs to know where individual people went. |
| Entry vs. leaving logic | **Decided in outline.** Direction comes from the **mmWave sensor**: someone crossing inward after a doorbell visit = arrived; crossing outward = left. Details (time window between the doorbell visit and the crossing, several people at once, quick trips out) are still to be worked out. |
| Who left | **Decided:** try these in order, and use the first that gives an answer: (1) **elimination**: if only one person is home, it's them (guests who came inside **count** toward who's home, so with a guest inside, elimination doesn't apply); (2) **face recognition** on the doorbell camera, if they're recognized in at least 3 frames (e.g. they turn around to lock the door); (3) **phone presence** (Wi-Fi/Bluetooth, later); (4) otherwise just "someone left". Needs a "who's home" state. |
| Box size (approaching = box grows) | **Rejected as the main signal**, but can be a supporting clue. It assumes people walk straight at the camera. In apartment hallways people approach from the side, neighbors walk past constantly, and someone unlocking the door barely moves. |
| Door contact sensor | **Optional, later.** Add one only if testing shows false alarms; then only count a crossing if the door actually opened. Options: a DIY reed switch on a Pi's GPIO (~$3), a Zigbee/Wi-Fi contact sensor in Home Assistant, or a smart lock that reports how it was unlocked. During development, door events can be simulated with a key press. |
| Apartments | The owner lives in an apartment, so expect hallway approaches and passing neighbors. A camera in a shared hallway may not be allowed by the lease or local rules; a **peephole camera** is a renter-friendly, face-level alternative. |
| Notifications | **Decided** (defaults; see "Doorbell visit logic" for exact rules). **Known people** (household, have a key): no "at the door" notification; notify "X arrived home" once they're inside. **Unknown people:** notify "X unknown people are at your door"; never "arrived home". **Mixed group** with a known person: no "at the door" notification; once inside, "jaden and 1 unknown arrived home". The owner will build a **mobile app** where users choose, per person, who notifies at the door and/or on arriving home (e.g. a kid without a key should notify at the door). Notifications print to the **terminal** until the app exists. Avoiding notification spam is a top priority. Clips with notifications are still planned. |
| Unknown people | **Notify without saving** (decided): never store their face or embedding. Holding them in memory during a visit is fine. |
| Delivery drivers | **Later:** detect them as a special case (they arrive and leave quickly). |
| Room sensing | **Later phase** (decided). Count people in and out of each room. Identity needs another source: person re-identification (hard) or phone presence (Bluetooth/Wi-Fi). Which one is **undecided**. |
| Automations | **Home Assistant** (decided): the system sends events to it (probably over MQTT) instead of controlling lights and devices itself. |
| 2D vs. depth/infrared sensing | **2D (normal camera) for the prototype** (decided). Depth (e.g. Intel RealSense, OAK-D) could add anti-spoofing, and infrared is needed for the doorbell camera at night; revisit both when choosing final hardware, especially if the system will unlock doors or handle security. |
| Final hardware | **Central hub design** (decided). Each camera is a low-end Raspberry Pi that only **streams** video (e.g. over RTSP) to one central hub, which runs all the CV. The hub is the Mac mini for now. Chosen for cost, power use, one place to update the code, and keeping the face database inside the home (not on the outdoor device). Ring/Nest work similarly, with the cloud as their hub. Pi Zero 2 W was hard to find; a Pi 4 (1 GB) + Camera Module 3 was the fallback. Still undecided: the hub's long-term hardware, how cameras are powered (PoE, doorbell wiring), and the outdoor enclosure. Battery power isn't viable for always-on vision. |
| Greeting output (speech engine, on-screen, etc.) | **Undecided** |
| Where data is stored (names, embeddings) | **SQLite** (decided), loaded into memory for comparisons. The database file stays on the local machine and out of git. |
| Privacy and consent approach | **Partly decided.** Only enrolled people's embeddings are stored; unknown faces never are. No camera inside the home (mmWave instead). Still open: privacy zones (masking the sidewalk or neighbors), clip retention/auto-delete. Check local laws on recording public areas and storing biometric data. |

Do not treat any "Undecided" item as settled. Ask the owner before choosing for them.

## Doorbell visit logic

Instead of tracking each person from frame to frame, the doorbell summarizes the scene over a **visit**. It answers "who showed up, and how many?" without needing to know which box is which person. Every frame still runs detection and recognition.

**A visit**
- **Opens** when a face is detected and no visit is open.
- **Closes** once no face has been detected for **15 s**.

**Per frame** while a visit is open, record how many faces were detected and the name each one matched (or "unknown").

**Over the visit**
- A **name counts** once it's recognized in **at least 3 frames** (one lucky frame can't name someone).
- **People count** = the highest face count seen in **at least 3 frames** (one false detection can't inflate it).
- **Unknown count** = people count − number of names that count.

**Timeline**
- **Under 5 s:** a passer-by. Ignored.
- **5 s:** the visit counts as "someone waiting" (the hook for logging and clips later). Measured as how long the visit has lasted, not as a face in every frame.
- **11 s:** if **no known person** counts in the visit and the unknown count is 1 or more, notify `X unknown people are at your door`. If a known person is there, send nothing.
- **After the 11 s notification:** a known person showing up sends nothing. If the number of faces **labeled "unknown"** goes **above the last reported number in at least 5 frames**, send one updated notification with the new count. Only when the 11 s notification was actually sent, and never on drops. (Labels are used here instead of "face count − known names": a known person walking up adds a face to every frame but is only subtracted once recognized 3 times, so the subtraction version briefly reported them as a new unknown. With labels, a known person only causes a false update if they go unrecognized in 5+ frames.)

**Arrived / left (needs the mmWave sensor)**
- People go inside after a visit → "jaden arrived home", or "jaden and 1 unknown arrived home". Nothing for an all-unknown group by default.
- Someone crosses outward → "X left", with X found as in "Who left" above.

**Later:** pre-roll clips (keep the last few seconds of frames in memory, so a clip starts before detection), an event log in SQLite (who, when, direction, clip path), and per-person notification settings from the app.

## Doorbell camera requirements

**Prototype (must have):**
1. **Recognize people** approaching, using the existing face recognition against the database and threshold.
2. **One notification per visit, not per frame** (see "Doorbell visit logic").
3. **Decide identity over several frames**, not from a single frame.
4. **Being at the door isn't entering.** Passers-by, delivery drivers and visitors who leave again must not be reported as entering; "arrived" needs an inward crossing on the mmWave sensor.
5. **Unknown people:** notify, but never store their face.

**Later:**
- Notifications with short clips, and pre-roll
- Event log in SQLite: who, when, direction, clip path
- A "who's home" state, updated by entries and exits (needed for "who left" and Home Assistant automations)
- Delivery driver detection
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

frame → detect faces → turn each face into an embedding → compare to known people → name → visit summary

- **Detection** answers "where are the faces?" (bounding boxes, plus facial landmarks).
- **Recognition** answers "whose face is it?" by comparing embeddings (numeric vectors) against stored ones for known people.
- These two questions are kept as separate steps in the code.
- The **visit** layer combines many frames into one answer per visit.
- Re-identifying people as they leave will add **person** detection and **tracking** across frames. Whole bodies, not just faces, because people walking away show their backs. Direction comes from the mmWave sensor, not the camera.

## Environment

- Language: Python
- Uses a per-project virtual environment (`python -m venv .venv`), activated before installing packages.
- Packages so far: `opencv-python`, `numpy`, `python-dotenv`
- Files so far:
  - `cam_test.py`: live camera view.
  - `detect.py`: live face detection (YuNet) and recognition (SFace) on the RTSP stream, with a background reader thread. Needs `models/face_detection_yunet_2023mar.onnx` and `models/face_recognition_sface_2021dec.onnx`, both from the `opencv/opencv_zoo` repo. Uses cosine similarity with a threshold of 0.50; OpenCV suggests about 0.363 for SFace. The detector's score threshold is 0.8 (the default 0.9 missed real faces, which scored only about 0.90; 0.7 let a hand over a face produce a second false box).
  - `db.py`: SQLite storage. A `faces` table with `id`, `name` and `embedding BLOB`. Embeddings are stored with `.tobytes()` and loaded with `np.frombuffer(..., dtype=np.float32).reshape(1, 128)`.
  - `tracker.py`: an IoU + face-embedding tracker. Not used now; kept in case tracking comes back.
  - `.env` (gitignored): `RTSP_USERNAME`, `RTSP_PASSWORD`, `RTSP_IP` for the Tapo camera's "Camera Account".
- With Continuity Camera, the iPhone shows up as an ordinary camera number in `cv2.VideoCapture(n)`. If it doesn't appear: first check FaceTime/Photo Booth's Video menu. A **USB cable** most likely fixed it the first time; Wi-Fi and Bluetooth on both devices, same Apple ID and Handoff on are the other requirements.
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

- Which CV stack to commit to (and whether a person detector/tracker is needed later: YOLO via `ultralytics`, a model through OpenCV's DNN module, or OpenCV's HOG detector)
- How notifications reach the phone (the owner plans their own app; the Home Assistant companion app was the alternative)
- Identity for room sensing: re-identification or phone presence
- How phone presence is detected (Wi-Fi/Bluetooth)
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
