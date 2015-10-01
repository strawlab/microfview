import threading

import numpy as np

DETECTED_OBJECT   = "UFVIEW_object"
TRACKED_OBJECT    = "UFVIEW_tracked_object"
TRACKED_3D_OBJECT = "UFVIEW_tracked_3d_object"
CONTOUR           = "UFVIEW_contour"
POINT_ARRAY       = "UFVIEW_point_array"

SPECIAL_STATE_KEYS = {DETECTED_OBJECT, TRACKED_OBJECT, TRACKED_3D_OBJECT, CONTOUR, POINT_ARRAY}

UNIT_METERS = "m"
UNIT_PIXELS = "px"


class _Transformable(object):

    @staticmethod
    def _transform_2pts(x,y,M):
        return M.dot([x,y,1])

    def transform(self, M):
        return self


class DetectedObjectType(_Transformable):
    def __init__(self, id, x, y):
        self.id = int(id)
        self.x = x
        self.y = y

    def __repr__(self):
        return "DetectedObject(id=%d, x=%s, y=%s)" % (self.id, self.x, self.y)

    def transform(self, M):
        x,y = self._transform_2pts(self.x, self.y, M)
        return DetectedObjectType(self.id, x, y)


class ContourType(_Transformable):
    def __init__(self, id, x, y, pts):
        self.id = int(id)
        self.x = x
        self.y = y
        self.pts = pts

    def __repr__(self):
        return "Contour(id=%d, x=%s, y=%s, pts=...)" % (self.id, self.x, self.y)

    def transform(self, M):
        x,y = self._transform_2pts(self.x, self.y, M)
        # make homogenous
        ptsh = np.c_[self.pts.squeeze(), np.ones(len(self.pts))]
        # transform
        pts2d = M.dot(ptsh.T).T
        # pad into weird opencv format
        pts = pts2d.reshape((-1,1,2))
        return ContourType(self.id, x, y, pts.astype(np.int32))


class TrackedObjectType(_Transformable):
    def __init__(self, id, x, y, err):
        self.id = int(id)
        self.x = x
        self.y = y
        self.err = err

    def __repr__(self):
        return "TrackedObject(id=%d, x=%s, y=%s, err=%s)" % (self.id, self.x, self.y, self.err)

    def transform(self, M):
        x,y = self._transform_2pts(self.x, self.y, M)
        return TrackedObjectType(self.id, x, y, self.err)


class Tracked3DObjectType:
    def __init__(self, id, x, y, z, err):
        self.id = int(id)
        self.x = x
        self.y = y
        self.z = z
        self.err = err

    def __repr__(self):
        return "Tracked3DObject(id=%d, x=%s, y=%s, z=%s err=%s)" % (self.id, self.x, self.y, self.z, self.err)


class PointArrayType(_Transformable):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "PointArray([[%s,%s]...[%s,%s]], %d pts)" % (self.x[0],self.y[0],self.x[-1],self.y[-1],len(self.x))

    def transform(self, M):
        # make homogenous
        ptsh = np.vstack((self.x, self.y, np.ones(len(self.x))))
        pts2d = M.dot(ptsh)
        x,y = pts2d
        return PointArrayType(x.astype(np.int32),y.astype(np.int32))


class FrameStore(object):

    def store_open(self, schema_dict):
        pass

    def store_state(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        raise NotImplementedError

    def store_close(self):
        pass

    def store_begin_frame(self, buf, frame_number, frame_count, frame_timestamp, now):
        pass

    def store_end_frame(self, buf, frame_number, frame_count, frame_timestamp, now):
        pass


class FrameStoreManager(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._framestores = []

    def add(self, framestore):
        self._framestores.append(framestore)

    def open(self, schema):
        for s in self._framestores:
            s.store_open(schema)

    def close(self):
        for s in self._framestores:
            s.store_close()

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        with self._lock:
            for s in self._framestores:
                s.store_state(callback_name, buf, frame_number, frame_count, frame_timestamp, now, state)

    def begin_frame(self, buf, frame_number, frame_count, frame_timestamp, now):
        for s in self._framestores:
            s.store_begin_frame(buf, frame_number, frame_count, frame_timestamp, now)

    def end_frame(self, buf, frame_number, frame_count, frame_timestamp, now):
        for s in self._framestores:
            s.store_end_frame(buf, frame_number, frame_count, frame_timestamp, now)
