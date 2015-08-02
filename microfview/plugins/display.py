import cv2
import numpy as np

from ..plugin import BlockingPlugin, PluginFinished


class DisplayPlugin(BlockingPlugin):

    def __init__(self, window_name, every=1):
        super(DisplayPlugin, self).__init__(every=every)
        self.shows_windows = True

        self._window_name = window_name

    def start(self, capture_object):
        # create a resizable window but limit its size to less than the screen size
        cv2.namedWindow(self._window_name, getattr(cv2,'WINDOW_NORMAL',0))
        w, h = capture_object.frame_shape
        if (w > 0) and (not np.isnan(w)):
                sf = (1024. / w) if w > 1024 else 1.0
                h *= sf
                w *= sf
                cv2.resizeWindow(self._window_name, (int(w), int(h)))
        cv2.namedWindow(self._window_name)

    def stop(self):
        cv2.destroyWindow(self._window_name)

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        cv2.imshow(self._window_name, frame)
        ch = state.get('KEY')
        if ch == 27:
            raise PluginFinished
