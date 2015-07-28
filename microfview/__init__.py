"""microfview module.

Available classes:
  - Microfview: class for delegating frames from Capture classes to
                Plugin classes
  - CameraCapture: class for interfacing cam_iface cameras
  - FMFCapture: class for interfacing FlyMovieFormat videos
  - BlockingPlugin: base class for blocking plugins
  - NonBlockingPlugin: base class for non blocking plugins

Available functions:
  - getLogger: returns the microfview logging.Logger instance

Microfview is a minimal implementation of something that is a
'fview-like' plugin framework. It comes without the whole GUI
stuff and creating a new plugin really boils down to writing
one function ('process_frame') that calculates something on
the captured frame.

Example:
  A minimal plugin example would look like this:

  >>> cam = CameraCapture()
  >>> fview = Microfview(cam)
  >>> class MySumPlugin(NonBlockingPlugin):
  >>>     def process_frame(frame_time, current_time, frame):
  >>>         print frame_time, frame.sum()
  >>> myplugin = MySumPlugin()
  >>> fview.attach_plugin(myplugin)
  >>> fview.start()

"""

__version__ = "0.1"

from .main import Microfview
from .camera import CameraCapture
from .video import FMFCapture
from .plugin import BlockingPlugin, NonBlockingPlugin

import logging

def getLogger():
    """returns the global microfview logging.Logger instance"""
    # setup logging
    logger = logging.getLogger('microfview')
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    f = logging.Formatter("%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
    return logger
