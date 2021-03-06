import time
import random
import os.path

import cv2
import numpy as np

from . import CaptureBase
from .. import data_dir

class _SynthBase(object):
    def __init__(self, size=None, noise=0.0, bg=None, fps=25, nframes=np.inf, **kwargs):
        self.fps = float(fps)
        self.nframes = float(nframes)

        self._bg = None
        self.frame_size = (640, 480)
        if bg is not None:
            # try the passed path and paths in the package datadir
            self._bg = cv2.imread(bg, 1)
            if self._bg is None:
                self._bg = cv2.imread(os.path.join(data_dir, bg), 1)
                if self._bg is None:
                    raise ValueError('%s not found' % bg)
            h, w = self._bg.shape[:2]
            self.frame_size = (w, h)

        if size is not None:
            w, h = map(int, size.split('x'))
            self.frame_size = (w, h)
            self._bg = cv2.resize(self._bg, self.frame_size)

        self._noise = float(noise)

    def get_last_frame_metadata(self):
        return {}

    def render(self, buf, frame_count):
        """override this function to draw on the background"""
        pass

    def read(self, frame_count):
        if self.fps > 0.0:
            t0 = time.time()

        w, h = self.frame_size

        if self._bg is None:
            buf = np.zeros((h, w, 3), np.uint8)
        else:
            buf = self._bg.copy()

        self.render(buf, frame_count)

        if self._noise > 0.0:
            noise = np.zeros((h, w, 3), np.int8)
            cv2.randn(noise, np.zeros(3), np.ones(3)*255*self._noise)
            buf = cv2.add(buf, noise, dtype=cv2.CV_8UC3)

        if self.fps > 0.0:
            t1 = time.time()
            #sleep the difference between the desired fps and our current fps
            #actually sleep a little less than the differnce because of jitter
            ddt = (1/self.fps) - (t1 - t0)
            if ddt > 0:
                time.sleep(ddt)


        return True, buf


class _MovingDot(_SynthBase):
    def __init__(self, **kwargs):
        super(_MovingDot, self).__init__(**kwargs)

        self._radius = int(kwargs.get('radius', 15))
        self._vx = self._vy = kwargs.get('speed', 5)
        try:
            self._pos = int(kwargs['initial_x']), int(kwargs['initial_y'])
        except KeyError:
            # start fully inside the window
            x = self._radius + (random.random() * (self.frame_size[0] - 2*self._radius - 2))
            y = self._radius + (random.random() * (self.frame_size[1] - 2*self._radius - 2))
            self._pos = int(x), int(y)
        try:
            self._fill = map(int,kwargs['fill_bgr'].split(','))
        except KeyError:
            self._fill = (0,0,255)
        self._radius = int(kwargs.get('radius', 15))
        self._dotnoise = float(kwargs.get('dotnoise',0))

    def render(self, buf, frame_count):
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

        if self._dotnoise:
            x += ((random.random() - 0.5) * self._dotnoise)
            y += ((random.random() - 0.5) * self._dotnoise)

        self._pos = x,y

        # render the circle
        cv2.circle(buf, (int(x),int(y)), self._radius, self._fill, -1)

    def get_last_frame_metadata(self):
        return {'dot_radius':self._radius, 'dot_position':self._pos}


class SynthCapture(CaptureBase):
    def __init__(self, desc, synthcls=None):
        super(SynthCapture, self).__init__()

        chunks = desc.split(':')
        if (len(chunks) > 1) and chunks[1]:

            params = {}
            for s in chunks[1:]:
                try:
                    k,v = s.split('=')
                    params[k] = v
                except ValueError:
                    pass

            if 'class' in params:
                classname = params.pop('class')
                if classname == 'dot':
                    self._capture = _MovingDot(**params)
                else:
                    raise NotImplementedError
            elif synthcls is not None:
                self._capture = synthcls(**params)
            else:
                self._capture = _SynthBase(**params)
        elif synthcls is not None:
            self._capture = synthcls()
        else:
            self._capture = _SynthBase()

        self._i = 0
        self._ts = time.time()
        self.fps = self._capture.fps
        self.frame_width = self._capture.frame_size[0]
        self.frame_height = self._capture.frame_size[1]
        self.is_video_file = False
        self.frame_count = self._capture.nframes

    def grab_next_frame_blocking(self):
        if self._i >= self.frame_count:
            raise EOFError
        _, buf = self._capture.read(self._i)
        self._i += 1
        self._ts = time.time()
        return buf

    def get_last_timestamp(self):
        return self._ts

    def get_last_framenumber(self):
        return self._i

    def get_last_metadata(self):
        return self._capture.get_last_frame_metadata()

