import os

import cv2

from . import Microfview, DisplayPlugin, get_capture_object
from .store import FrameStore


class StateFrameStore(FrameStore):

    def __init__(self):
        self.state = []

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        self.state.append(state)


def get_test_instance(fps=2, nframes=10, display=False):
    fps = int(os.environ.get('UFVIEW_TEST_FPS', fps))
    display = int(os.environ.get('UFVIEW_TEST_DISPLAY', display))

    cam = get_capture_object("synth:class=dot:fps=%d:nframes=%d" % (fps, nframes))
    fview = Microfview(cam)
    s = StateFrameStore()
    fview.attach_framestore(s)
    if display:
        fview.attach_plugin(DisplayPlugin('test'))
    fview.main()
    return s.state


def get_test_frame(frame_type='grascaley'):
    assert frame_type in ('binary','grayscale','color')

    synthdesc = "synth:class=dot:fps=0:nframes=1:initial_x=200:initial_y=300"
    if frame_type == 'binary':
        synthdesc += ":fill_bgr=255,255,255"
    else:
        synthdesc += ":fill_bgr=0,0,255"
    cam = get_capture_object(synthdesc)

    img = cam.grab_next_frame_blocking()
    if frame_type != 'color':
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return img, cam.get_last_metadata()
