import cv2

from ..plugin import BlockingPlugin, PluginFinished


class DisplayPlugin(BlockingPlugin):

    def __init__(self, window_name, every=1):
        super(DisplayPlugin, self).__init__(every=every)
        self.shows_windows = True

        self._window_name = window_name

    def start(self, capture_object):
        cv2.namedWindow(self._window_name)

    def stop(self):
        cv2.destroyWindow(self._window_name)

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        cv2.imshow(self._window_name, frame)
        ch = state.get('KEY')
        if ch == 27:
            raise PluginFinished
