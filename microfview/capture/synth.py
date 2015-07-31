import cv2
import time
import random

import numpy as np

from . import CaptureBase

class _SynthBase(object):
    def __init__(self, size=None, noise=0.0, bg=None, fps=25, **params):
        self.fps = float(fps)

        self._bg = None
        self.frame_size = (640, 480)
        if bg is not None:
            self._bg = cv2.imread(bg, 1)
            h, w = self._bg.shape[:2]
            self.frame_size = (w, h)

        if size is not None:
            w, h = map(int, size.split('x'))
            self.frame_size = (w, h)
            self._bg = cv2.resize(self._bg, self.frame_size)

        self._noise = float(noise)
        self._t0 = time.time()

    def render(self, buf):
        pass

    def read(self, dst=None):
        if self.fps > 0.0:
            t1 = time.time()
            dt = t1 - self._t0
            self._t0 = t1
            #sleep the difference between the desired fps and our current fps
            #actually sleep a little less than the differnce because of jitter
            ddt = (1/self.fps) - dt
            if ddt > 0:
                time.sleep(0.5*ddt)

        w, h = self.frame_size

        if self._bg is None:
            buf = np.zeros((h, w, 3), np.uint8)
        else:
            buf = self._bg.copy()

        self.render(buf)

        if self._noise > 0.0:
            noise = np.zeros((h, w, 3), np.int8)
            cv2.randn(noise, np.zeros(3), np.ones(3)*255*self._noise)
            buf = cv2.add(buf, noise, dtype=cv2.CV_8UC3)
        return True, buf


class _MovingDot(_SynthBase):
    def __init__(self, **kwargs):
        super(_MovingDot, self).__init__(**kwargs)

        self._vx = self._vy = kwargs.get('speed', 5)
        self._pos = int(random.random()*self.frame_size[0]), int(random.random()*self.frame_size[1])
        self._size = kwargs.get('size', 10)

    def render(self, buf):
        x,y = self._pos
        w,h = self.frame_size

        if x > w:
            self._vx *= -1.0
        elif x < 0:
            self._vx *= -1.0
        if y > h:
            self._vy *= -1.0
        elif y < 0:
            self._vy *= -1.0

        x += self._vx
        y += self._vy

        cv2.circle(buf, (int(x),int(y)), self._size, (0, 0, 255), -1)

        self._pos = x,y

class SynthCapture(CaptureBase):
    def __init__(self, desc):
        chunks = desc.split(':')
        if (len(chunks) > 1) and chunks[1]:
            params = dict(s.split('=') for s in chunks[1:])
            if 'class' in params:
                classname = params.pop('class')
                if classname == 'dot':
                    self._capture = _MovingDot(**params)
                else:
                    raise NotImplementedError
            else:
                self._capture = _SynthBase(**params)
        else:
            self._capture = _SynthBase()

        self._i = 0
        self._ts = time.time()
        self.fps = self._capture.fps
        self.frame_width = self._capture.frame_size[0]
        self.frame_height = self._capture.frame_size[0]
        self.is_video_file = False

    def grab_next_frame_blocking(self):
        _, buf = self._capture.read()
        self._i += 1
        self._ts = time.time()
        return buf

    def get_last_timestamp(self):
        return self._ts

    def get_last_framenumber(self):
        return self._i