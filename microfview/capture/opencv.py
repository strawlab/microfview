"""microfview.video module

Provides FMFCapture class for FlyMovieFormat videos.
"""
import time

import cv2

import logging

from . import CaptureBase

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
        self._log = logging.getLogger('microfview.capture.OpenCVCapture')

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
        self.noncritical_errors = VideoDeviceReadError,

    def _grab_frame_blocking(self, n=None):
        """returns next frame."""
        if n is not None:
            seeking = True
            self.seek_frame(n)
        else:
            seeking = False

        #opencv post increments, so get these first
        ms = self._capture.get(getattr(cv2,"CAP_PROP_POS_MSEC",0))
        fn = self._capture.get(getattr(cv2,"CAP_PROP_POS_FRAMES",1))

        frame_timestamp = ms/1000.
        frame_number = int(fn)

        flag, frame = self._capture.read()

        if not flag:
            if self.is_video_file:
                if seeking:
                    #seeking is generally shit. Sometimes we seek to positions
                    #that are past the number of frames in the file, and yet
                    #we get data.
                    return None
                else:
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
        if self.is_video_file:
            if n == 0:
                self._capture.release()
                self._capture = cv2.VideoCapture(self._identifier)
            else:
                self._capture.set(getattr(cv2,"CAP_PROP_POS_FRAMES",1), n)
        else:
            raise ValueError("Seeking not available on video devices")

    def grab_next_frame_blocking(self):
        return self._grab_frame_blocking()

    def grab_frame_n(self, n):
        if self.is_video_file:
            return self._grab_frame_blocking(n)
        else:
            raise ValueError("Seeking not available on video devices")

    def get_last_timestamp(self):
        """returns the timestamp of the last frame."""
        return self._frame_timestamp

    def get_last_framenumber(self):
        """returns the framenumber of the last frame."""
        return self._frame_number


