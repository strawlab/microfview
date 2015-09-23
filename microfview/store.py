DETECTED_OBJECT   = "UFVIEW_object"
TRACKED_OBJECT    = "UFVIEW_tracked_object"
TRACKED_3D_OBJECT = "UFVIEW_tracked_3d_object"
CONTOUR           = "UFVIEW_contour"
POINT_ARRAY       = "UFVIEW_point_array"

SPECIAL_STATE_KEYS = {DETECTED_OBJECT, TRACKED_OBJECT, TRACKED_3D_OBJECT, CONTOUR, POINT_ARRAY}

UNIT_METERS = "m"
UNIT_PIXELS = "px"


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


class Tracked3DObjectType:
    def __init__(self, id, x, y, z, err):
        self.id = int(id)
        self.x = x
        self.y = y
        self.z = z
        self.err = err

    def __repr__(self):
        return "Tracked3DObject(id=%d, x=%s, y=%s, z=%s err=%s)" % (self.id, self.x, self.y, self.z, self.err)


class PointArrayType:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "PointArray([[%s,%s]...[%s,%s]], %d pts)" % (self.x[0],self.y[0],self.x[-1],self.y[-1],len(self.x))


class FrameStore(object):

    def open(self, schema_dict):
        pass

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        raise NotImplementedError

    def close(self):
        pass
