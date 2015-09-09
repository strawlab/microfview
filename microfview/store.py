import collections

DETECTED_OBJECT   = "UFVIEW_object"
TRACKED_OBJECT    = "UFVIEW_tracked_object"
CONTOUR           = "UFVIEW_contour"

SPECIAL_STATE_KEYS = set((DETECTED_OBJECT, TRACKED_OBJECT, CONTOUR))

DetectedObjectType = collections.namedtuple('TrackedObject', ['id', 'x', 'y'])
TrackedObjectType = collections.namedtuple('TrackedObject', ['id', 'x', 'y', 'err'])
ContourType = collections.namedtuple("Contour", ['id', 'x', 'y', 'pts'])


def state_update(old, new):
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

class FrameStore(object):

    def open(self, schema_dict):
        pass

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        raise NotImplementedError

    def close(self):
        pass
