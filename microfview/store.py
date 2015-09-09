import collections

STORE_TRACKED_OBJECT    = "UFVIEW_object"
STORE_CONTOUR           = "UFVIEW_contour"

TrackedObjectType = collections.namedtuple('TrackedObject', ['id', 'x', 'y'])
ContourType = collections.namedtuple("Contour", ['id', 'cx', 'cy', 'pts'])


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
