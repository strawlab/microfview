import cv2
import numpy as np

try:
    from skimage.draw import set_color
except ImportError:
    set_color = None

from ..plugin import BlockingPlugin, MESSAGE_SEEK
from ..store import FrameStore, SPECIAL_STATE_KEYS, TrackedObjectType, DetectedObjectType, ContourType, UNIT_PIXELS, PointArrayType
from ..util import is_color


def draw_state(frame, val, M):
    if isinstance(val, ContourType):
        if M is not None:
            val = val.transform(M)
        # contours are drawn in red
        cv2.circle(frame, (int(val.x),int(val.y)),2,(255,0,255),1)
        cv2.drawContours(frame, [val.pts], 0, (255,0,255), 1)
    elif isinstance(val, (TrackedObjectType, DetectedObjectType)):
        if M is not None:
            val = val.transform(M)
        # objects in green
        if getattr(val, "unit", UNIT_PIXELS) == UNIT_PIXELS:
            cv2.circle(frame, (int(val.x),int(val.y)),3,(0,255,0),2)
    elif isinstance(val, PointArrayType):
        if M is not None:
            val = val.transform(M)
        if set_color is not None:
            r,c = val.y, val.x
            if is_color(frame):
                # draw in yellow
                set_color(frame, (r,c), (0,255,255))
            else:
                set_color(frame, (r,c), 255)


def draw_all_state(img, state, M):
    for key in SPECIAL_STATE_KEYS:
        try:
            obj = state[key]
            draw_state(img, obj, M)
        except KeyError:
            pass


class DisplayPlugin(BlockingPlugin, FrameStore):

    def __init__(self, window_name, original_frame=False, every=1, seek=False):
        super(DisplayPlugin, self).__init__(every=every)
        self.shows_windows = True
        self.human_name = "%s(%s)" % (self.__class__.__name__, window_name)
        self._show_original_frame = original_frame
        self._seek = seek
        self._seek_frame_max = None
        self.__window_name = window_name

        # in main operation we are called via the framestore interface
        self.__last_img = None

        if set_color is None:
            self.logger.warn('displaying point arrays disabled due to missing scikit-image')

    def _on_seek(self, v):
        fn = (v/255.0) * self._seek_frame_max
        self.send_message(MESSAGE_SEEK, int(fn))

    def start(self, capture_object):
        # wait until here to get the window name because it depends on the uid
        self._window_name = self.debug_window_name(self.__window_name)
        if self.visible:
            # create a resizable window but limit its size to less than the screen size
            cv2.namedWindow(self._window_name, getattr(cv2,'WINDOW_NORMAL',0))
            w, h = capture_object.frame_shape
            if (w > 0) and (not np.isnan(w)):
                    sf = (1024. / w) if w > 1024 else 1.0
                    h *= sf
                    w *= sf
                    cv2.resizeWindow(self._window_name, int(w), int(h))
            if self._seek and capture_object.supports_seeking:
                self._seek_frame_max = capture_object.frame_count
                cv2.createTrackbar("seek", self._window_name, 0, 255, self._on_seek)
        elif self._seek:
            self.logger.info("seeking disabled as we are hidden")
            self._seek = False

    def stop(self):
        if self.visible:
            cv2.destroyWindow(self._window_name)

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        if self.visible:
            img = frame if not self._show_original_frame else state['FRAME_ORIGINAL']
            if self._show_original_frame and ('FRAME_TRANSFORM' in state):
                M = state['FRAME_TRANSFORM']
            else:
                M = None
            draw_all_state(img, state, M)
            cv2.imshow(self._window_name, img)

    def store_state(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        if self.visible:
            draw_all_state(self.__last_img, state, state.get('FRAME_TRANSFORM', None))

    def store_begin_frame(self, buf, frame_number, frame_count, frame_timestamp, now, key):
        if self.visible:
            self.__last_img = buf

    def store_end_frame(self, buf, frame_number, frame_count, frame_timestamp, now):
        if self.visible:
            cv2.imshow(self._window_name, self.__last_img)

