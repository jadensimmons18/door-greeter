# Groups frames into visits: a visit opens when a face appears and closes once
# no face has been seen for VISIT_TIMEOUT seconds. While a visit is open it records
# each frame's faces, and when it closes it summarizes who was there and how many.

from collections import Counter

VISIT_TIMEOUT = 15.0  # seconds without any face before a visit closes
MIN_FRAMES = 3        # frames a name (or a face count) must appear in to be trusted
WAITING_TIME = 5.0    # seconds of visit before it counts as someone waiting (shorter = passing by)
NOTIFY_TIME = 11.0    # seconds of visit before deciding whether to send "unknown people at your door"


class Visits:
    def __init__(self):
        self.start = None           # when the current visit opened (time.monotonic()), or None if no visit is open
        self.last_face_time = None  # when a face was last detected during the current visit
        self.face_counts = []       # number of faces in each frame of the current visit (frames with faces only)
        self.name_frames = Counter()  # name -> number of frames it was recognized in, during the current visit
        # Flags so each milestone fires once per visit, not on every frame after it's reached
        self.waiting_reported = False  # the 5 s mark has been handled
        self.door_decided = False      # the 11 s decision has been made (whether or not it notified)
        self.reported_unknowns = 0     # unknown count in the last notification (for update notifications later)

    def is_open(self):
        return self.start is not None

    # Call once per frame with the names of the faces in that frame ("unknown" for unrecognized faces).
    # Call it on frames with no faces too, with an empty list: those are the frames where a visit can end.
    # now must come from time.monotonic(), which never jumps backwards like the wall clock can.
    def update(self, names, now):
        if len(names) > 0:
            if not self.is_open():
                self.start = now
                self.face_counts = []  # a new visit starts with no data from the last one
                self.name_frames = Counter()
                self.waiting_reported = False
                self.door_decided = False
                self.reported_unknowns = 0
                print("visit started")
            self.last_face_time = now

            self.face_counts.append(len(names))
            # set(): count each name at most once per frame, so two faces both matching "jaden" in one
            # frame (one is a misrecognition) don't count as two frames of evidence.
            # Unknowns are left out here; they're worked out from the face count instead.
            self.name_frames.update(set(names) - {"unknown"})

            self.check_timeline()

        elif self.is_open() and now - self.last_face_time > VISIT_TIMEOUT:
            # Measure up to the last face, not up to now: the last 15 s were an empty doorway
            duration = self.last_face_time - self.start
            print(f"visit ended, lasted {duration:.1f} s: {self.describe()}")
            self.start = None
            self.last_face_time = None

    # Runs on every frame with faces. Each milestone checks "reached AND not yet handled", so it
    # fires once (edge-triggered) instead of on every frame after it's reached (level-triggered).
    def check_timeline(self):
        # How long people have been seen, not how long the visit has been open: someone who left
        # at 8 s keeps the visit open 15 s longer, but must never reach the 11 s notification
        seen_for = self.last_face_time - self.start

        if seen_for >= WAITING_TIME and not self.waiting_reported:
            self.waiting_reported = True
            print("someone is waiting")

        if seen_for >= NOTIFY_TIME and not self.door_decided:
            # Decide once, either way: a known person recognized after this point changes nothing
            self.door_decided = True
            if len(self.known_names()) > 0:
                return  # a household member is there and has a key: no "at the door" notification
            unknowns = self.unknown_count()
            if unknowns >= 1:
                self.reported_unknowns = unknowns
                if unknowns == 1:
                    print("[notify] 1 unknown person is at your door")
                else:
                    print(f"[notify] {unknowns} unknown people are at your door")

    # Names recognized in at least MIN_FRAMES frames of this visit
    def known_names(self):
        return [name for name, frames in self.name_frames.items() if frames >= MIN_FRAMES]

    # The largest k such that at least MIN_FRAMES frames had k or more faces.
    # That's the MIN_FRAMES-th largest face count: sorted [3, 3, 2, 2, 1] -> 3rd value is 2.
    def people_count(self):
        if len(self.face_counts) < MIN_FRAMES:
            return 0  # too few frames to trust anything (e.g. a one-frame false detection)
        return sorted(self.face_counts, reverse=True)[MIN_FRAMES - 1]

    # People who were there but not recognized. max(0, ...) in case a misrecognized name
    # got past the frame rule and there are more names than people.
    def unknown_count(self):
        return max(0, self.people_count() - len(self.known_names()))

    # e.g. "jaden, 1 unknown", or "0 people"
    def describe(self):
        parts = self.known_names()
        if self.unknown_count() > 0:
            parts.append(f"{self.unknown_count()} unknown")
        return ", ".join(parts) if parts else "0 people"
