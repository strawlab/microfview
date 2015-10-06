"""microfview.video module

Provides FMFCapture class for FlyMovieFormat videos.
"""

import logging
import os.path

import cv2
import numpy as np

from . import CaptureBase, SeekError

def decode_4cc(capture):
    prop = getattr(cv2,'CAP_PROP_FOURCC',6) #keep compat with OpenCV < 3.0
    fourcc = int(capture.get(prop))
    if fourcc > 0:
        return "%c%c%c%c" % (chr(fourcc & 255),
                             chr((fourcc >> 8) & 255),
                             chr((fourcc >> 16) & 255),
                             chr((fourcc >> 24) & 255))
    else:
        return "????"


class VideoDeviceReadError(Exception):
    pass


class OpenCVCapture(CaptureBase):

    def __init__(self, identifier, is_file, **prop_config):
        """class for using opencv VideoCapture objects

        Args:
          identifier (str): identifier as per cv2.VideoCapture
          is_file (bool): true if this device backs a video file (mp4, etc)
        """
        super(OpenCVCapture, self).__init__()

        self._log = logging.getLogger('microfview.capture.OpenCVCapture')

        self._log.info('opening %s (file: %s)' % (identifier, is_file))

        self._identifier = identifier
        self._capture = cv2.VideoCapture(identifier)
        if not self._capture.isOpened():
            raise Exception("Unable to open %s" % identifier)

        self._frame_timestamp = 0.0
        self._frame_number = -1

        self._log.info('%s format: %s' % ("file" if is_file else "device",
                                          decode_4cc(self._capture)))

        #CaptureBase attributes
        self.fps = self._capture.get(getattr(cv2,"CAP_PROP_FPS",5))
        self.frame_width = self._capture.get(getattr(cv2,"CAP_PROP_FRAME_WIDTH",3))
        self.frame_height = self._capture.get(getattr(cv2,"CAP_PROP_FRAME_HEIGHT",4))
        self.is_video_file = is_file
        if is_file:
            self.frame_count = self._capture.get(getattr(cv2,"CAP_PROP_FRAME_COUNT",7))
            self.filename = os.path.abspath(identifier)
            self.supports_seeking = True
            self._log.warn("seeking is not reliable on some videos in opencv")
        self.noncritical_errors = VideoDeviceReadError,

        if np.isnan(self.fps):
            self._log.warn("unknown FPS")

    def grab_next_frame_blocking(self):
        """returns next frame."""
        #opencv post increments, so get these first
        ms = self._capture.get(getattr(cv2,"CAP_PROP_POS_MSEC",0))
        fn = self._capture.get(getattr(cv2,"CAP_PROP_POS_FRAMES",1))

        frame_timestamp = ms/1000.
        frame_number = int(fn)

        flag, frame = self._capture.read()

        if not flag:
            if self.is_video_file:
                #there is not true way for opencv to tell us we are at
                #the end of file - so add many scary heuristics
                if frame_number >= self.frame_count:
                    raise EOFError("File ended at frame: %d" % frame_number)
                #the frame didn't advance - truncated file
                fn2 = self._capture.get(getattr(cv2,"CAP_PROP_POS_FRAMES",1))
                if (fn > 0) and (fn == fn2):
                    raise EOFError("Truncated file at at frame: %d" % frame_number)
            raise VideoDeviceReadError

        self._frame_timestamp = frame_timestamp
        self._frame_number = frame_number

        return frame

    def seek_frame(self, n):
        """Seeks to the given frame in the files.

        Seeking on random videos is generally risky, so we do some sanity checking.
        Seeking to n=0 reopens the file (if this wraps a video file)

        :param n: framenumber
        :return: np.array
        """
        if self.is_video_file:
            if n == 0:
                self._capture.release()
                self._capture = cv2.VideoCapture(self._identifier)
            else:
                self._capture.set(getattr(cv2,"CAP_PROP_POS_FRAMES",1), n)
        else:
            raise ValueError("Seeking not available on video devices")

    def get_last_timestamp(self):
        """returns the timestamp of the last frame."""
        return self._frame_timestamp

    def get_last_framenumber(self):
        """returns the framenumber of the last frame."""
        return self._frame_number


