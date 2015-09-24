"""microfview.video module

Provides FMFCapture class for FlyMovieFormat videos.
"""
import motmot.FlyMovieFormat.FlyMovieFormat as fmf
import time

import logging
logger = logging.getLogger('microfview')

from . import CaptureBase

class FMFCapture(CaptureBase):

    supports_seeking = True

    def __init__(self, filename, check_integrity=False, force_framerate=0):
        """class for interfacing fmf videos.

        Args:
          filename (str): fmf filename.
          check_integrity (bool, optional): check integrity of fmf file on
            load. Defaults to False.
          force_framerate (float, optional): forces a maximum framerate.
            Defaults to 20.

        """
        super(FMFCapture, self).__init__()

        self._mov = fmf.FlyMovie(filename, check_integrity)

        self._frame_timestamp = 0.0
        self._frame_number = -1
        if force_framerate > 0:
            self._frame_delay = 1./float(force_framerate)
        else:
            self._frame_delay = None

        #CaptureBase attributes
        self.frame_count = self._mov.n_frames
        self.frame_width = self._mov.width
        self.frame_height = self._mov.height
        self.is_video_file = True
        self.filename = filename

    def seek_frame(self, n):
        self._mov.seek(n)

    def grab_next_frame_blocking(self):
        """returns next frame."""
        try:
            frame, timestamp = self._mov.get_next_frame(allow_partial_frames=False)
        except fmf.NoMoreFramesException as e:
            if e.message == 'EOF':
                raise EOFError
        self._frame_timestamp = timestamp
        self._frame_number += 1
        if self._frame_delay is not None:
            time.sleep(self._frame_delay)
        return frame

    def get_last_timestamp(self):
        """returns the timestamp of the last frame."""
        return self._frame_timestamp

    def get_last_framenumber(self):
        """returns the framenumber of the last frame."""
        return self._frame_number

