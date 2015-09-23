import os

import cv2

from . import Microfview, BlockingPlugin, get_capture_object
from .store import FrameStore


class StateFrameStore(FrameStore):

    def __init__(self):
        self.state = []

    def store(self, callback_name, buf, frame_number, frame_count, frame_timestamp, now, state):
        # storing the original image wastes memory for tests
        try: state.pop('FRAME_ORIGINAL')
        except KeyError: pass
        try: state.pop('KEY')
        except KeyError: pass
        self.state.append(state.copy())


class DummyPlugin(BlockingPlugin):
    def start(self, capture_object): pass
    def stop(self): pass
    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state): pass


def get_test_instance(fps=0, nframes=100, display=False, cam=None, synthdesc=''):
    fps = int(os.environ.get('UFVIEW_TEST_FPS', fps))
    display = int(os.environ.get('UFVIEW_TEST_DISPLAY', display))
    if cam is None:
        cam = get_capture_object("synth:class=dot:fps=%d:nframes=%d:%s" % (fps, nframes, synthdesc))
    fview = Microfview(cam, visible=bool(display), debug=False, stop_frame=nframes)
    s = StateFrameStore()
    fview.attach_framestore(s)
    if display:
        fview.attach_display_plugin()
    return fview, s


def run_test_instance_and_plugins(*plugins, **kwargs):
    fview, framestore = get_test_instance(**kwargs)
    map(fview.attach_plugin, plugins)
    fview.main()
    return framestore.state


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
