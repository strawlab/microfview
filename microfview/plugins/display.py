import cv2
import numpy as np

from ..plugin import BlockingPlugin
from ..store import SPECIAL_STATE_KEYS, TrackedObjectType, DetectedObjectType, ContourType

class DisplayPlugin(BlockingPlugin):

    def __init__(self, window_name, show_original_frame=False, every=1):
        super(DisplayPlugin, self).__init__(every=every)
        self.shows_windows = True
        self.human_name = "%s(%s)" % (self.__class__.__name__, window_name)
        self._show_original_frame = show_original_frame
        self.__window_name = window_name

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

    def stop(self):
        if self.visible:
            cv2.destroyWindow(self._window_name)

    def _draw_state(self, frame, val):
        if isinstance(val, ContourType):
            # contours are drawn in red
            cv2.circle(frame, (int(val.x),int(val.y)),2,(0,0,255),1)
            cv2.drawContours(frame, [val.pts], 0, (0,0,255), 1)
        elif isinstance(val, (TrackedObjectType, DetectedObjectType)):
            # objects in green
            cv2.circle(frame, (int(val.x),int(val.y)),3,(0,255,0),2)

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        if self.visible:
            img = frame if not self._show_original_frame else state['FRAME_ORIGINAL']
            for key in SPECIAL_STATE_KEYS:
                try:
                    obj = state[key]
                    self._draw_state(img, obj)
                except KeyError:
                    pass
            cv2.imshow(self._window_name, img)
