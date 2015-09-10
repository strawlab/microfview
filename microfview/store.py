import collections

DETECTED_OBJECT   = "UFVIEW_object"
TRACKED_OBJECT    = "UFVIEW_tracked_object"
CONTOUR           = "UFVIEW_contour"

SPECIAL_STATE_KEYS = {DETECTED_OBJECT, TRACKED_OBJECT, CONTOUR}


def state_update(old, new, nick):
    for k in new:
        if k in SPECIAL_STATE_KEYS:
            _new = new[k]
            if isinstance(_new, list) and len(_new):
                for __new in _new:
                    if __new not in old[k]:
                        old[k].append(__new)
            else:
                old[k].append(_new)
        else:
            old[k] = new[k]


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
