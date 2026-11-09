# Links detections across frames: gives each box a track ID that stays the same
# while the same person is in view. Works on any boxes (faces now, bodies later).

IOU_THRESHOLD = 0.3  # minimum overlap for a box to count as the same track as last frame
MAX_AGE = 2.0        # seconds a track can go unseen before it's closed


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


class Track:
    def __init__(self, track_id, box, now):
        self.id = track_id
        self.box = box        # where this person was last seen
        self.last_seen = now  # when they were last seen (seconds, from time.monotonic())


class Tracker:
    def __init__(self):
        self.tracks = []  # tracks that are currently open
        self.next_id = 1  # IDs only go up, so a closed track's ID is never reused

    # Takes this frame's boxes and returns a track ID for each one, in the same order.
    # Call it every frame, even with no boxes, so tracks of people who left get closed.
    def update(self, boxes, now):
        # First close tracks that haven't been seen for too long: that person has left.
        # This must happen before matching, or a stale track could be revived by a new box in the same place.
        self.tracks = [track for track in self.tracks if now - track.last_seen <= MAX_AGE]

        # Score every (track, box) pair by overlap, then match the best pairs first (greedy matching)
        pairs = []
        for t, track in enumerate(self.tracks):
            for b, box in enumerate(boxes):
                overlap = iou(track.box, box)
                if overlap >= IOU_THRESHOLD:
                    pairs.append((overlap, t, b))
        pairs.sort(reverse=True)

        ids = [None] * len(boxes)
        used_tracks = set()
        for overlap, t, b in pairs:
            if t in used_tracks or ids[b] is not None:
                continue  # this track or this box was already matched to a better partner
            track = self.tracks[t]
            track.box = boxes[b]
            track.last_seen = now
            ids[b] = track.id
            used_tracks.add(t)

        # Boxes that matched no track are new people: start a track for each
        for b, box in enumerate(boxes):
            if ids[b] is None:
                track = Track(self.next_id, box, now)
                self.next_id += 1
                self.tracks.append(track)
                ids[b] = track.id

        return ids
