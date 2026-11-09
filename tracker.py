# Links detections across frames: gives each box a track ID that stays the same
# while the same person is in view. Works on any boxes (faces now, bodies later).
#
# Matching runs in two passes:
#   Pass 1: match by position (IoU). Cheap, and handles normal movement.
#   Pass 2: match leftovers by appearance (embedding similarity). Catches people who
#           jumped to a new spot (stood up, stepped back) or came back after a gap.
# Only boxes that fail both passes start a new track.

import numpy as np

IOU_THRESHOLD = 0.3         # minimum overlap for a box to count as the same track by position
MAX_AGE = 30.0              # seconds a track can go unseen before it's closed
SIMILARITY_THRESHOLD = 0.5  # minimum cosine similarity for two faces to count as the same person
RECENT = 1.0                # seconds: a track seen this recently is matched by IoU alone (no face check)
EMBEDDING_UPDATE = 0.2      # how much each new frame changes a track's stored face (0 = never, 1 = replace)
DEBUG = True                # print similarity scores, for tuning SIMILARITY_THRESHOLD


# Intersection over Union: how much two boxes overlap, from 0 (not at all) to 1 (identical).
# Boxes are (x, y, w, h), with (x, y) the top-left corner.
def iou(box_a, box_b):
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b

    # The overlap rectangle runs from the larger of the left/top edges to the smaller of the right/bottom edges
    overlap_w = min(ax + aw, bx + bw) - max(ax, bx)
    overlap_h = min(ay + ah, by + bh) - max(ay, by)
    if overlap_w <= 0 or overlap_h <= 0:
        return 0.0  # the boxes don't touch

    intersection = overlap_w * overlap_h
    union = aw * ah + bw * bh - intersection  # subtract the overlap so it isn't counted twice
    return intersection / union


# Scales a vector to length 1, so only its direction is left
def normalize(vector):
    vector = vector.ravel()  # (1, 128) -> (128,)
    return vector / np.linalg.norm(vector)


# Cosine similarity: 1 = same direction (same face), around 0 = unrelated.
# Same number as recognizer.match(..., cv2.FaceRecognizerSF_FR_COSINE).
def similarity(a, b):
    return float(np.dot(normalize(a), normalize(b)))


class Track:
    def __init__(self, track_id, box, embedding, now):
        self.id = track_id
        self.box = box                         # where this person was last seen
        self.embedding = normalize(embedding)  # what their face looks like (kept in memory only, gone when the track closes)
        self.last_seen = now                   # when they were last seen (seconds, from time.monotonic())

    # Called when this track is matched to a box in the current frame
    def update(self, box, embedding, now):
        self.box = box
        self.last_seen = now
        # Running average: blend the new face in a little at a time, so one blurry frame
        # can't replace a good stored face
        mixed = (1 - EMBEDDING_UPDATE) * self.embedding + EMBEDDING_UPDATE * normalize(embedding)
        self.embedding = normalize(mixed)


class Tracker:
    def __init__(self):
        self.tracks = []  # tracks that are currently open
        self.next_id = 1  # IDs only go up, so a closed track's ID is never reused

    # Takes this frame's boxes and their face embeddings (same order) and returns a track ID
    # for each box. Call it every frame, even with no boxes, so tracks of people who left get closed.
    def update(self, boxes, embeddings, now):
        # First close tracks that haven't been seen for too long: that person has left.
        # This must happen before matching, or a stale track could be revived by a new box in the same place.
        self.tracks = [track for track in self.tracks if now - track.last_seen <= MAX_AGE]

        ids = [None] * len(boxes)  # the track ID for each box; None = not matched yet
        used_tracks = set()        # indexes of tracks already matched this frame

        # Pass 1: match by position
        pairs = []
        for t, track in enumerate(self.tracks):
            for b, box in enumerate(boxes):
                overlap = iou(track.box, box)
                if overlap < IOU_THRESHOLD:
                    continue
                # A track that's been unseen for a while could have been replaced by someone else
                # standing in the same spot, so also require the face to match
                if now - track.last_seen > RECENT:
                    sim = similarity(track.embedding, embeddings[b])
                    if DEBUG:
                        print(f"pass 1: track #{track.id} unseen {now - track.last_seen:.1f}s, similarity {sim:.2f}")
                    if sim < SIMILARITY_THRESHOLD:
                        continue
                pairs.append((overlap, t, b))
        self._assign(pairs, ids, used_tracks, boxes, embeddings, now)

        # Pass 2: match the leftovers by appearance, wherever they are in the image
        pairs = []
        for t, track in enumerate(self.tracks):
            if t in used_tracks:
                continue
            for b in range(len(boxes)):
                if ids[b] is not None:
                    continue
                sim = similarity(track.embedding, embeddings[b])
                if DEBUG:
                    print(f"pass 2: track #{track.id} vs new box, similarity {sim:.2f}")
                if sim >= SIMILARITY_THRESHOLD:
                    pairs.append((sim, t, b))
        self._assign(pairs, ids, used_tracks, boxes, embeddings, now)

        # Boxes that matched no track in either pass are new people: start a track for each
        for b, box in enumerate(boxes):
            if ids[b] is None:
                track = Track(self.next_id, box, embeddings[b], now)
                self.next_id += 1
                self.tracks.append(track)
                ids[b] = track.id

        return ids

    # Greedy matching: takes (score, track index, box index) pairs and matches the
    # highest-scoring pairs first, skipping any track or box that's already taken
    def _assign(self, pairs, ids, used_tracks, boxes, embeddings, now):
        pairs.sort(reverse=True)
        for score, t, b in pairs:
            if t in used_tracks or ids[b] is not None:
                continue  # this track or this box was already matched to a better partner
            track = self.tracks[t]
            track.update(boxes[b], embeddings[b], now)
            ids[b] = track.id
            used_tracks.add(t)
