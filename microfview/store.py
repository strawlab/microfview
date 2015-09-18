import collections

DETECTED_OBJECT   = "UFVIEW_object"
TRACKED_OBJECT    = "UFVIEW_tracked_object"
CONTOUR           = "UFVIEW_contour"

SPECIAL_STATE_KEYS = {DETECTED_OBJECT, TRACKED_OBJECT, CONTOUR}


class DetectedObjectType:
    def __init__(self, id, x, y):
        self.id = int(id)
        self.x = x
        self.y = y

    def __repr__(self):
        return "DetectedObject(id=%d, x=%s, y=%s)" % (self.id, self.x, self.y)


class ContourType:
    def __init__(self, id, x, y, pts):
        self.id = int(id)
        self.x = x
        self.y = y
        self.pts = pts

    def __repr__(self):
        return "Contour(id=%d, x=%s, y=%s, pts=...)" % (self.id, self.x, self.y)


class TrackedObjectType:
    def __init__(self, id, x, y, err):
        self.id = int(id)
        self.x = x
        self.y = y
        self.err = err

    def __repr__(self):
        return "TrackedObject(id=%d, x=%s, y=%s, err=%s)" % (self.id, self.x, self.y, self.err)


class FrameStore(object):

    def open(self, schema_dict):
        pass

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        raise NotImplementedError

    def close(self):
        pass
