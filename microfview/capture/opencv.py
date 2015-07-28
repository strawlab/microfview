"""microfview.video module

Provides FMFCapture class for FlyMovieFormat videos.
"""
import time

import cv2

import logging

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

class OpenCVCapture(object):

    def __init__(self, filename, **prop_config):
        """class for using opencv VideoCapture objects

        Args:
          filename (str): filename or identifier as per cv2.VideoCapture
        """
        self._log = logging.getLogger('microfview.capture.OpenCVCapture')

        self._capture = cv2.VideoCapture(filename)
        self._frame_timestamp = 0.0
        self._frame_number = -1
        self.noncritical_errors = tuple()

        self._log.info('format: %s' % decode_4cc(self._capture))

    def grab_next_frame_blocking(self):
        """returns next frame."""
        flag, frame = self._capture.read()
        self._frame_timestamp = time.time()
        self._frame_number += 1
        return frame

    def get_last_timestamp(self):
        """returns the timestamp of the last frame."""
        return self._frame_timestamp

    def get_last_framenumber(self):
        """returns the framenumber of the last frame."""
        return self._frame_number

